#!/usr/bin/env python3
"""AF2 multimer wrapper: restricts MODEL_PRESETS to model_1_multimer_v3 only.

Monkey-patches alphafold.model.config before run_alphafold imports it so that
only model_1_multimer_v3 is run. All other flags are passed through unchanged.
"""
import sys
sys.path.insert(0, '/software/alphafold-2.3.2-el8-x86_64')

# Must patch before run_alphafold is imported (absl flag parsing happens later)
import alphafold.model.config as _config
_config.MODEL_PRESETS['multimer'] = ('model_1_multimer_v3',)

from absl import app
import run_alphafold

if __name__ == '__main__':
    app.run(run_alphafold.main)
