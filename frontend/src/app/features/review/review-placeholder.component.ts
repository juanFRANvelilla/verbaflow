import { Component } from '@angular/core';

@Component({
  selector: 'app-review',
  standalone: true,
  template: `<section class="review"><h1>Repaso</h1><p>FSRS — siguiente iteración.</p></section>`,
  styles: [
    `
      .review {
        padding: 1.5rem;
        max-width: 28rem;
        margin: 0 auto;
      }
    `,
  ],
})
export class ReviewPlaceholderComponent {}