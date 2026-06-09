/**
 * WebSocket client.
 *
 * One persistent connection per logged-in user; reconnects with exponential
 * backoff and patches RTK Query caches when events arrive. The token is
 * passed via query string because RN's native WebSocket can't set custom
 * headers — matches the backend's /ws endpoint expectation.
 */

import { api } from '../api';
import { chatApi } from '../api/chatApi';
import type { Dispatch } from '@reduxjs/toolkit';
import type { RootState } from '../store';
import { WS_BASE_URL } from './config';

// ──────────────────────────────────────────────────────────────────────────────
// Frame types — must match `backend/app/**/*.py` event names.
// ──────────────────────────────────────────────────────────────────────────────
type WsFrame =
  | { type: 'hello'; data: { user_id: number } }
  | { type: 'pong' }
  | { type: 'notification.new'; data: any }
  | { type: 'message.new'; data: any }
  | { type: 'message.updated'; message_id: number; body: string }
  | { type: 'message.deleted'; message_id: number }
  | { type: 'reaction.toggled'; message_id: number; user_id: number; emoji: string; added: boolean }
  | { type: 'read.advanced'; user_id: number; up_to_message_id: number }
  | { type: 'participants.changed'; check_id: number }
  | { type: 'participant.joined'; user_id: number }
  | { type: 'participant.left'; user_id: number }
  | { type: 'participant.ready'; user_id: number }
  | { type: 'participant.unready'; user_id: number }
  | { type: 'assignment.updated'; check_item_id: number; participant_id: number; quantity: string; amount: string }
  | { type: 'assignment.removed'; check_item_id: number; participant_id: number }
  | { type: 'dice.proposal.created'; proposal_id: number; proposed_by: number }
  | { type: 'dice.proposal.declined'; proposal_id: number }
  | { type: 'dice.completed'; proposal_id: number; payer_user_id: number; total_paid_for_others: string }
  | { type: 'presence.self'; status: string };

// ──────────────────────────────────────────────────────────────────────────────
// Connection
// ──────────────────────────────────────────────────────────────────────────────
class WsConnection {
  private socket: WebSocket | null = null;
  private dispatch: Dispatch | null = null;
  private getState: (() => RootState) | null = null;
  private heartbeat: ReturnType<typeof setInterval> | null = null;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private backoffMs = 1000;
  private shouldReconnect = false;

  attach(dispatch: Dispatch, getState: () => RootState): void {
    this.dispatch = dispatch;
    this.getState = getState;
  }

  connect(): void {
    if (!this.dispatch || !this.getState) return;
    const token = this.getState().auth.accessToken;
    if (!token) return;

    this.shouldReconnect = true;
    const url = `${WS_BASE_URL}/ws?token=${encodeURIComponent(token)}`;
    try {
      this.socket = new WebSocket(url);
    } catch (e) {
      this.scheduleReconnect();
      return;
    }
    this.socket.onopen = () => {
      this.backoffMs = 1000;
      this.startHeartbeat();
    };
    this.socket.onmessage = (ev) => this.handleFrame(ev.data);
    this.socket.onerror = () => {
      // The close handler will fire too; reconnect logic lives there.
    };
    this.socket.onclose = () => {
      this.cleanupSocket();
      if (this.shouldReconnect) this.scheduleReconnect();
    };
  }

  disconnect(): void {
    this.shouldReconnect = false;
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    this.reconnectTimer = null;
    if (this.socket) {
      try {
        this.socket.close();
      } catch {
        /* noop */
      }
    }
    this.cleanupSocket();
  }

  private scheduleReconnect(): void {
    this.reconnectTimer = setTimeout(() => this.connect(), this.backoffMs);
    this.backoffMs = Math.min(this.backoffMs * 2, 30_000);
  }

  private cleanupSocket(): void {
    if (this.heartbeat) {
      clearInterval(this.heartbeat);
      this.heartbeat = null;
    }
    this.socket = null;
  }

  private startHeartbeat(): void {
    if (this.heartbeat) clearInterval(this.heartbeat);
    this.heartbeat = setInterval(() => {
      if (this.socket?.readyState === 1) {
        this.socket.send(JSON.stringify({ type: 'ping' }));
      }
    }, 30_000);
  }

  private handleFrame(raw: unknown): void {
    if (typeof raw !== 'string' || !this.dispatch) return;
    let frame: WsFrame;
    try {
      frame = JSON.parse(raw);
    } catch {
      return;
    }
    this.dispatch_(frame);
  }

  /**
   * Translate WS frames into RTK Query cache patches and tag invalidations.
   * Anything we don't recognise is dropped silently.
   */
  private dispatch_(frame: WsFrame): void {
    if (!this.dispatch) return;
    const d = this.dispatch as any;

    switch (frame.type) {
      case 'notification.new':
        d(api.util.invalidateTags(['Notification']));
        return;

      case 'message.new': {
        const msg = frame.data;
        // Patch the messages list cache directly so the chat screen updates
        // without a re-fetch.
        d(
          chatApi.util.updateQueryData(
            'listMessages',
            { conversation_id: msg.conversation_id },
            (draft: any[]) => {
              if (draft.find((m) => m.id === msg.id)) return;
              draft.push(msg);
            },
          ),
        );
        // Conversation list shows preview + bumps last_message_at + unread.
        d(api.util.invalidateTags(['Conversation']));
        return;
      }

      case 'message.updated':
      case 'message.deleted':
      case 'reaction.toggled':
      case 'read.advanced':
        // Cheaper to just invalidate the relevant conversation cache than to
        // hunt down the message in every list query.
        d(api.util.invalidateTags(['Conversation', 'Message']));
        return;

      case 'participants.changed':
      case 'participant.joined':
      case 'participant.left':
      case 'participant.ready':
      case 'participant.unready':
      case 'assignment.updated':
      case 'assignment.removed':
      case 'dice.proposal.created':
      case 'dice.proposal.declined':
      case 'dice.completed':
        d(api.util.invalidateTags(['Check']));
        return;

      case 'presence.self':
        d(api.util.invalidateTags(['Presence']));
        return;

      default:
        return;
    }
  }
}

export const ws = new WsConnection();
