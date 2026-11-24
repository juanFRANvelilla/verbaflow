import { UpperCasePipe } from '@angular/common';
import { Component, inject, OnInit, signal } from '@angular/core';
import { VerbaflowApiService, VocabularyEntry } from '../../core/api/verbaflow-api.service';

@Component({
  selector: 'app-library',
  standalone: true,
  imports: [UpperCasePipe],
  templateUrl: './library.component.html',
  styleUrl: './library.component.scss',
})
export class LibraryComponent implements OnInit {
  private readonly api = inject(VerbaflowApiService);
  readonly items = signal<VocabularyEntry[]>([]);

  ngOnInit(): void {
    this.api.listEntries().subscribe((rows) => this.items.set(rows));
  }
}