// main_c.js — вариант C (гибрид): GLB из Blender + ввод, расцветки KHR_materials_variants, разборка — кодом.
import { boot } from './main_3d.js';
boot('c', () => import('./model_c.js').then((m) => m.buildModelC));
