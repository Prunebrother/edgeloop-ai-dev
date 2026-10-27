// SPDX-License-Identifier: AGPL-3.0-only
import {test} from 'node:test';
import assert from 'node:assert/strict';
import {EXPRESSIONS,resolveArtwork} from '../../src/js/ai/artwork-manifest.js';
test('model artwork resolves expression, neutral, default and missing model independently',()=>{
    const manifest={'one:tag':{name:'One',artwork:'/default.webp',expressions:{neutral:'/neutral.png',happy:'/happy.webp'}},
        'two:tag':{name:'Two',artwork:'/two.webp'}};
    assert.equal(resolveArtwork('one:tag','happy',manifest).src,'/happy.webp');
    assert.deepEqual(resolveArtwork('one:tag','happy',manifest).sources,['/happy.webp','/neutral.png','/default.webp']);
    assert.equal(resolveArtwork('one:tag','excited',manifest).src,'/neutral.png');
    assert.equal(resolveArtwork('two:tag','speaking',manifest).src,'/two.webp');
    assert.equal(resolveArtwork('unknown','neutral',manifest).src,null);
    assert.equal(resolveArtwork('__proto__','neutral',manifest).src,null);
    assert.equal(resolveArtwork('one:tag','untrusted state',manifest).expression,'neutral');
    assert.equal(EXPRESSIONS.length,12);
});
