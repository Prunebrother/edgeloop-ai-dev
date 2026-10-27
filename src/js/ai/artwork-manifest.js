// SPDX-License-Identifier: AGPL-3.0-only
// Local public assets only; never include credentials or private model data here.
export const EXPRESSIONS = Object.freeze(['neutral','happy','excited','playful','thoughtful',
    'concerned','surprised','serious','amused','listening','speaking','relaxed']);
export const DEFAULT_CHARACTER = Object.freeze({name:'Your companion', artwork:null, expressions:{}});
// Exact Ollama identifiers (including tags). Add PNG/WebP portrait paths here.
// Example: 'my-model:latest': {name:'My character', artwork:'/src/assets/characters/default.webp',
//     expressions:{neutral:'/src/assets/characters/neutral.webp', happy:'/src/assets/characters/happy.webp'}}
export const MODEL_ARTWORK = Object.freeze({});
export function resolveArtwork(model, expression='neutral', manifest=MODEL_ARTWORK) {
    const character=Object.hasOwn(manifest,model||'') ? manifest[model] : DEFAULT_CHARACTER;
    const requested=EXPRESSIONS.includes(expression)?expression:'neutral';
    const sources=[...new Set([character.expressions?.[requested],character.expressions?.neutral,character.artwork].filter(Boolean))];
    return {name:character.name || model || DEFAULT_CHARACTER.name, expression:requested,
        src:sources[0] || null, sources};
}
