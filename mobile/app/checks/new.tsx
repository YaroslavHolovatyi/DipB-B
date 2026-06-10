/**
 * Capture a receipt → create a Check → enter the split room.
 *
 * Flow:
 *   1. Take a photo (camera) or pick one from the library via expo-image-picker.
 *   2. Preview it, optionally add a note.
 *   3. Ask the backend for a presigned upload URL (POST /checks/upload-url),
 *      PUT the image bytes there, then POST /checks with the returned public
 *      URL so the server-side Vision call can fetch it. We route into
 *      `/checks/[id]`.
 *
 * Local-dev fallback: when the backend has no S3/R2 configured it runs in stub
 * storage mode and hands back a `file://` URL that can't be PUT to over HTTP.
 * In that case (and if the presign endpoint is unavailable on an older backend)
 * we fall back to sending the local asset URI directly — which still works,
 * because the stub OCR service ignores the image and returns a canned parse.
 */

import { Ionicons } from '@expo/vector-icons';
import * as ImagePicker from 'expo-image-picker';
import { router, Stack, useLocalSearchParams } from 'expo-router';
import { useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Image,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import {
  useCreateCheckMutation,
  useCreateEventCheckMutation,
  useReceiptUploadUrlMutation,
} from '../../api/checksApi';
import { C, F } from '../../theme/styleHelpers';

function toId(v: string | string[] | undefined): number | null {
  const raw = Array.isArray(v) ? v[0] : v;
  if (!raw) return null;
  const n = Number(raw);
  return Number.isFinite(n) ? n : null;
}

function contentTypeFor(uri: string): string {
  const ext = uri.split('?')[0].split('.').pop()?.toLowerCase();
  if (ext === 'png') return 'image/png';
  if (ext === 'webp') return 'image/webp';
  if (ext === 'heic' || ext === 'heif') return 'image/heic';
  return 'image/jpeg';
}

export default function NewCheckScreen() {
  const params = useLocalSearchParams<{ raid_id?: string; party_id?: string }>();
  const raidId = toId(params.raid_id);
  const partyId = toId(params.party_id);
  const fromEvent = raidId != null || partyId != null;

  const [imageUri, setImageUri] = useState<string | null>(null);
  const [note, setNote] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const [createCheck] = useCreateCheckMutation();
  const [createEventCheck] = useCreateEventCheckMutation();
  const [getUploadUrl] = useReceiptUploadUrlMutation();

  /**
   * Presign + PUT the receipt image. Returns the URL to hand to POST /checks.
   * Falls back to the local URI when running against stub storage (file://)
   * or if the presign endpoint isn't available.
   */
  const uploadReceiptImage = async (localUri: string): Promise<string> => {
    const content_type = contentTypeFor(localUri);
    try {
      const presigned = await getUploadUrl({ content_type }).unwrap();
      // Stub storage hands back a non-HTTP URL we can't PUT to — use the local
      // URI directly (the stub OCR ignores it anyway).
      if (!/^https?:\/\//i.test(presigned.upload_url)) {
        return localUri;
      }
      const blob = await (await fetch(localUri)).blob();
      const putRes = await fetch(presigned.upload_url, {
        method: 'PUT',
        headers: { 'Content-Type': content_type },
        body: blob,
      });
      if (!putRes.ok) throw new Error(`upload failed: ${putRes.status}`);
      return presigned.public_url;
    } catch {
      // Older backend without /checks/upload-url, or a transient upload error:
      // fall through to the local URI so the demo flow still completes.
      return localUri;
    }
  };

  const pickFromCamera = async () => {
    const perm = await ImagePicker.requestCameraPermissionsAsync();
    if (!perm.granted) {
      Alert.alert('Camera access needed', 'Enable camera access to scan a receipt.');
      return;
    }
    const res = await ImagePicker.launchCameraAsync({
      mediaTypes: ['images'],
      quality: 0.7,
    });
    if (!res.canceled && res.assets[0]) setImageUri(res.assets[0].uri);
  };

  const pickFromLibrary = async () => {
    const perm = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!perm.granted) {
      Alert.alert('Photo access needed', 'Enable photo access to choose a receipt.');
      return;
    }
    const res = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ['images'],
      quality: 0.7,
    });
    if (!res.canceled && res.assets[0]) setImageUri(res.assets[0].uri);
  };

  const submit = async () => {
    if (!imageUri) return;
    setSubmitting(true);
    try {
      const image_url = await uploadReceiptImage(imageUri);
      const check = fromEvent
        ? await createEventCheck({
            image_url,
            raid_id: raidId,
            party_id: partyId,
            note: note.trim() || null,
          }).unwrap()
        : await createCheck({
            image_url,
            note: note.trim() || null,
          }).unwrap();
      router.replace(`/checks/${check.id}` as never);
    } catch {
      Alert.alert(
        'Could not create check',
        'Something went wrong processing the receipt. Please try again.',
      );
      setSubmitting(false);
    }
  };

  return (
    <SafeAreaView style={s.safe} edges={['top']}>
      <Stack.Screen
        options={{
          title: fromEvent ? 'Split the Bill' : 'Scan Receipt',
          headerShown: true,
        }}
      />

      <View style={s.body}>
        <View style={s.titleRow}>
          <Ionicons name="receipt-outline" size={22} color={C.textPrimary} />
          <Text style={s.title}>{fromEvent ? 'Split the Bill' : 'Scan a Receipt'}</Text>
        </View>
        <Text style={s.subtitle}>
          {fromEvent
            ? "Snap the shared bill — everyone who showed up gets to pick what they ordered."
            : "Snap your tavern bill and we'll read the line items so you can split it."}
        </Text>

        <View style={s.preview}>
          {imageUri ? (
            <Image source={{ uri: imageUri }} style={s.previewImg} resizeMode="cover" />
          ) : (
            <View style={s.previewEmpty}>
              <Ionicons name="camera-outline" size={40} color={C.textSecondary} />
              <Text style={s.previewEmptyText}>No receipt yet</Text>
            </View>
          )}
        </View>

        <View style={s.pickRow}>
          <TouchableOpacity style={s.pickBtn} onPress={pickFromCamera} activeOpacity={0.85}>
            <Ionicons name="camera" size={22} color={C.brandPrimary} />
            <Text style={s.pickLabel}>Take photo</Text>
          </TouchableOpacity>
          <TouchableOpacity style={s.pickBtn} onPress={pickFromLibrary} activeOpacity={0.85}>
            <Ionicons name="images" size={22} color={C.brandPrimary} />
            <Text style={s.pickLabel}>From library</Text>
          </TouchableOpacity>
        </View>

        <Text style={s.label}>Note (optional)</Text>
        <TextInput
          placeholder="e.g. Friday pints with the guild"
          placeholderTextColor={C.textSecondary}
          value={note}
          onChangeText={setNote}
          style={s.input}
        />

        <TouchableOpacity
          style={[s.submit, (!imageUri || submitting) && s.submitDisabled]}
          onPress={submit}
          disabled={!imageUri || submitting}
          activeOpacity={0.85}
        >
          {submitting ? (
            <ActivityIndicator color="#FFFFFF" />
          ) : (
            <Text style={s.submitText}>Create check</Text>
          )}
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  safe: { flex: 1, backgroundColor: C.bgBase },
  body: { flex: 1, paddingHorizontal: 20, paddingTop: 12 },

  titleRow: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  title: { fontFamily: F.headingBold, fontSize: 24, color: C.textPrimary },
  subtitle: {
    fontFamily: F.bodyRegular, fontSize: 14, color: C.textSecondary,
    marginTop: 4, marginBottom: 16,
  },

  preview: {
    height: 240, borderRadius: 16, overflow: 'hidden',
    backgroundColor: C.bgInput, borderWidth: 1, borderColor: C.borderDefault,
  },
  previewImg: { width: '100%', height: '100%' },
  previewEmpty: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: 8 },
  previewEmptyIcon: { fontSize: 40 },
  previewEmptyText: { fontFamily: F.bodyRegular, fontSize: 13, color: C.textSecondary },

  pickRow: { flexDirection: 'row', gap: 12, marginTop: 14 },
  pickBtn: {
    flex: 1, flexDirection: 'row', alignItems: 'center', justifyContent: 'center',
    gap: 8, paddingVertical: 12, borderRadius: 12,
    backgroundColor: C.bgCard, borderWidth: 1, borderColor: C.borderDefault,
  },
  pickIcon: { fontSize: 18 },
  pickLabel: { fontFamily: F.bodySemiBold, fontSize: 14, color: C.textPrimary },

  label: {
    fontFamily: F.bodySemiBold, fontSize: 13, color: C.textSecondary,
    marginTop: 20, marginBottom: 6,
  },
  input: {
    fontFamily: F.bodyRegular, fontSize: 15, color: C.textPrimary,
    backgroundColor: C.bgInput, borderRadius: 12,
    borderWidth: 1, borderColor: C.borderDefault,
    paddingHorizontal: 12, paddingVertical: 12,
  },

  submit: {
    marginTop: 24, borderRadius: 14, paddingVertical: 16,
    backgroundColor: C.brandPrimary, alignItems: 'center',
  },
  submitDisabled: { opacity: 0.5 },
  submitText: { fontFamily: F.bodyBold, fontSize: 16, color: '#FFFFFF' },
});
