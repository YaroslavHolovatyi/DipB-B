/** Quiz — list questions, submit a run, fetch the latest result. */

import { api } from './index';
import type { QuizQuestion, QuizResult } from './types';

export const quizApi = api.injectEndpoints({
  endpoints: (build) => ({
    listQuestions: build.query<QuizQuestion[], void>({
      query: () => '/quiz/questions',
      providesTags: ['Quiz'],
    }),
    submitQuiz: build.mutation<
      QuizResult,
      { answer_ids: number[]; gender?: 'm' | 'f' | null }
    >({
      query: (body) => ({ url: '/quiz/submit', method: 'POST', body }),
      invalidatesTags: ['QuizResult', 'User'],
    }),
    myQuizResult: build.query<QuizResult, void>({
      query: () => '/quiz/me',
      providesTags: ['QuizResult'],
    }),
  }),
});

export const { useListQuestionsQuery, useSubmitQuizMutation, useMyQuizResultQuery } = quizApi;
