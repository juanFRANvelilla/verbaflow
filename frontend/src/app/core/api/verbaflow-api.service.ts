import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface LookupResponse {
  lookup_id: string;
  effective_en: string;
  stt: { best_text: string };
  llm: {
    normalized_en: string;
    translation_es: string;
    example_en: string;
    alternatives: { en: string; reason: string; confidence: number }[];
    needs_user_pick: boolean;
  };
}

export interface VocabItem {
  id: string;
  canonical_en: string;
  translation_es: string;
  example_en: string | null;
}

@Injectable({ providedIn: 'root' })
export class VerbaflowApiService {
  private readonly http = inject(HttpClient);
  private readonly base = environment.apiBaseUrl;

  lookup(audio: Blob, contextNote?: string): Observable<LookupResponse> {
    const form = new FormData();
    form.append('audio', audio, 'clip.webm');
    if (contextNote?.trim()) {
      form.append('context_note', contextNote.trim());
    }
    return this.http.post<LookupResponse>(`${this.base}/api/lookup`, form);
  }

  saveLookup(lookupId: string, tags: string[] = []): Observable<VocabItem> {
    return this.http.post<VocabItem>(`${this.base}/api/lookup/${lookupId}/save`, { tags });
  }

  listVocab(): Observable<VocabItem[]> {
    return this.http.get<VocabItem[]>(`${this.base}/api/vocab`);
  }
}