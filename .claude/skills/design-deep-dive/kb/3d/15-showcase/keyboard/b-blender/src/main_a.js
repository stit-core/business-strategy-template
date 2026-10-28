// main_a.js — вариант A (код на максимуме): модель целиком кодом по паспорту.
import { boot } from './main_3d.js';
boot('a', () => import('./model_a.js').then((m) => m.buildModelA));
