// main_b.js — вариант B: страница на кадрах Blender, без three.
import { startPage } from './page.js';
import { createAdapterB } from './adapter_b.js';
startPage(createAdapterB({ pressFrames: true, turnFrames: true }));
