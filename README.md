# Asteroid Impact

See original Asteroid Impact [here](https://github.com/richardhuskey/asteroid_impact/tree/master).

# Notes for pylsl fork

This fork adds support for pylsl, and makes a number of quality of life improvements tailored to a demo context with adaptive difficulty and a dual task.

To install and run:
1) install [uv](https://docs.astral.sh/uv/getting-started/installation/)
2) clone this repo (at least `/src`)
3) run Command Prompt
4) cd into the downloaded (unzipped) directory
5) do `uv venv .venv`
6) do `uv pip sync`
7) run the game using `uv run game.py --display-mode fullscreen --script-json script.json` (or, to enable logging: `uv run game.py --display-mode fullscreen --script-json script.json --subject-number 1 --log-filename logs\test_log.csv --reaction-log-filename logs\reaction_test_log.csv --log-overwrite false`)

# License

Asteroid Impact was developed in the Media Neuroscience Lab (http://www.medianeuroscience.org/) Rene Weber, PI and the Cognitive Communication Science Lab (http://cogcommscience.com/) Richard Huskey, PI.

Asteroid Impact is licensed under a Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this work. If not, see http://creativecommons.org/licenses/by-sa/4.0/.

Key Contributors include:

Richard Huskey, Jacob Fisher, Nick Winters, Justin Keene, Britney Craighead, and Rene Weber

