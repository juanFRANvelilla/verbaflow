import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface Language {
  code: string;
  name: string;
  enabled: boolean;
}

export interface LookupResponse {
  language_code: string;
  effective_text: string;
  llm_ok: boolean;
  llm_error?: string | null;
  translation_source?: 'dictionary' | 'llm' | 'none';
  stt: { best_text: string };
  llm: {
    normalized_en: string;
    translation_es: string;
    example_en: string;
    alternatives: { en: string; reason: string; confidence: number }[];
    needs_user_pick: boolean;
  };
}

export interface VocabularyEntry {
  id: string;
  language_code: string;
  text: string;
  translation: string;
  example_text: string | null;
}

export interface SaveEntryPayload {
  language_code: string;
  text: string;
  translation: string;
  example_text?: string | null;
}

@Injectable({ providedIn: 'root' })
export class VerbaflowApiService {
  private readonly http = inject(HttpClient);
  private readonly base = environment.apiBaseUrl;

  listLanguages(): Observable<Language[]> {
    return this.http.get<Language[]>(`${this.base}/api/languages`);
  }

  lookupText(
    text: string,
    languageCode: string,
    sttSource: 'browser' | 'manual' = 'browser',
  ): Observable<LookupResponse> {
    return this.http.post<LookupResponse>(`${this.base}/api/lookup/text`, {
      language_code: languageCode,
      text,
      stt_source: sttSource,
    });
  }

  lookup(audio: Blob, languageCode: string, contextNote?: string): Observable<LookupResponse> {
    const form = new FormData();
    const type = audio.type.toLowerCase();
    const filename =
      type.includes('mp4') || type.includes('m4a') || type.includes('aac') || type.includes('mpeg')
        ? 'clip.m4a'
        : 'clip.webm';
    form.append('audio', audio, filename);
    form.append('language_code', languageCode);
    if (contextNote?.trim()) {
      form.append('context_note', contextNote.trim());
    }
    return this.http.post<LookupResponse>(`${this.base}/api/lookup`, form);
  }

  saveEntry(payload: SaveEntryPayload): Observable<VocabularyEntry> {
    return this.http.post<VocabularyEntry>(`${this.base}/api/entries`, payload);
  }

  listEntries(languageCode?: string): Observable<VocabularyEntry[]> {
    const q = languageCode ? `?language_code=${encodeURIComponent(languageCode)}` : '';
    return this.http.get<VocabularyEntry[]>(`${this.base}/api/entries${q}`);
  }
}