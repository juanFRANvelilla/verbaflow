import { Component, inject, OnInit, signal } from '@angular/core';
import { VerbaflowApiService, VocabItem } from '../../core/api/verbaflow-api.service';

@Component({
  selector: 'app-library',
  standalone: true,
  templateUrl: './library.component.html',
  styleUrl: './library.component.scss',
})
export class LibraryComponent implements OnInit {
  private readonly api = inject(VerbaflowApiService);
  readonly items = signal<VocabItem[]>([]);

  ngOnInit(): void {
    this.api.listVocab().subscribe((rows) => this.items.set(rows));
  }
}