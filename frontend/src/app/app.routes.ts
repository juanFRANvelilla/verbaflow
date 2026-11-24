import { Routes } from '@angular/router';

export const routes: Routes = [
  { path: '', pathMatch: 'full', redirectTo: 'capture' },
  {
    path: 'capture',
    loadComponent: () => import('./features/capture/capture.component').then((m) => m.CaptureComponent),
  },
  {
    path: 'library',
    loadComponent: () => import('./features/library/library.component').then((m) => m.LibraryComponent),
  },
  {
    path: 'review',
    loadComponent: () =>
      import('./features/review/review-placeholder.component').then((m) => m.ReviewPlaceholderComponent),
  },
];