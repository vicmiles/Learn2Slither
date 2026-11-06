Learn2Slither is a Snake game trained with tabular Q-learning. It requires Python 3.10 or newer. The game uses the Python standard library and Tkinter for its graphical interface. It does not use a neural network or a pathfinding algorithm.

Run all commands from the project directory.

To prepare the project:
make

The setup checks Python, virtual environment support and Tkinter, creates .venv and compiles the Python modules to bytecode. On Debian and Ubuntu, missing system dependencies are installed using apt-get. System installation requires administrator rights. If the school account cannot use sudo, ask the administrator to install python3, python3-venv and python3-tk. No administrator rights or Internet connection are needed when the runtime dependencies are already installed.

To prepare and launch the graphical lobby:
make run

Choose a model, board size, number of games, speed, random seed and step limit in the lobby. Learning is disabled by default. Enable learning to continue training. If no save path was supplied, training started from the lobby saves to models/menu-trained.json.

make setup is another name for the preparation command. To choose a Python interpreter, run make PYTHON=/usr/bin/python3. On other Linux distributions, install the equivalent system packages using the distribution's package manager. Automatic system installation only supports apt-get. If make is unavailable, run sh setup.sh.

For headless use, prepare with make WITH_GUI=0 and run:
.venv/bin/python main.py -visual off --quiet -load models/best.json -dontlearn

To launch a model directly without the lobby:
./snake -load models/best.json -dontlearn

If the launcher is not executable, run chmod +x snake. You can also use python3 main.py with the same arguments.

To watch the agent one move at a time:
./snake -load models/best.json -dontlearn -step-by-step

Space pauses or resumes normal playback. In step mode, Space advances one move. N advances one move, V toggles the vision overlay, S saves the model, plus and minus change speed, and Escape closes the window. The same controls are available as buttons and a speed slider. S uses the path given by -save or defaults to models/checkpoint.json. Saving also works while paused.

The results screen opens after the last game. It shows final lengths, lifetime, bonus goals and a chart of the last 100 games. JSON and CSV exports are available. Runs started from the lobby can return to the lobby. Step mode requires another step between games.

To evaluate a model without changing its Q-values:
./snake -visual off --quiet -load models/best.json -dontlearn -sessions 200 --seed 2027 --report results/my-evaluation.json --csv results/my-games.csv

-visual off disables the window. --quiet hides vision and individual game results. The summary is still printed. Without --quiet, the agent's vision and selected action are printed before each move.

To train a new agent and save the required checkpoints:
./snake -visual off --quiet -sessions 30000 --seed 42 --checkpoint-dir models -save models/candidate.json

This starts from an empty Q-table. Checkpoints are saved after 1, 10 and 100 completed training games. Existing files at the selected paths are replaced.

To continue training a saved agent:
./snake -visual off --quiet -load models/candidate.json -sessions 10000 --seed 123 -save models/continued.json

-sessions specifies the number of additional games. A loaded model supplies its learning parameters. The --alpha, --gamma, --epsilon, --epsilon-min and --epsilon-decay options apply only when starting without a model. Ctrl+C saves current learning if -save is set.

Each model is a JSON file containing the Q-table, learning parameters, completed episode count, update count and the agent's random generator state. It restores learning, not an unfinished board. Models trained for 1, 10 and 100 games are supplied in models, together with longer-trained models and best.json.

Games use a step limit of 3000 by default. Change it with --max-steps. Reaching the limit is recorded as step limit, not death. The final learning update still includes the next state's value. This prevents endless experiments when the agent loops.

The default board is 10 by 10. The snake starts with three contiguous cells at a random position and orientation. Two green apples increase length by one. One red apple decreases length by one. Eaten apples respawn in free cells. A wall collision, body collision or zero length ends the game. A cell vacated by the tail during the move can be entered. Filling the entire board ends the game with board filled. If there is not enough room for all apples, missing apples are placed when cells become available.

--size N changes the board size from 5 to 40. The same trained model works at different sizes because state encoding does not use absolute coordinates or board dimensions. Performance can vary.

environment.py contains the board, movement, collisions, apple placement and vision. interpreter.py encodes observations and assigns rewards. agent.py selects actions, updates Q-values and saves or loads models. main.py connects these modules and collects results. display.py, menu.py and ui.py provide the graphical interface. benchmark.py evaluates the same model on different board sizes. clean.py removes generated cache files and the optional virtual environment.

The agent only receives observations derived from four rays extending from its head to the walls, in UP, LEFT, DOWN, RIGHT order. W means wall, S body, G green apple, R red apple and 0 empty space. H marks the head in terminal output. Rays include cells behind other objects, as in the subject's example. The agent does not receive the full board, snake coordinates, length or hidden apple positions.

State encoding uses 12 bits. Four indicate an adjacent wall or body. Four indicate a green apple along a direction before the first body segment or wall. Four indicate an adjacent red apple. This gives at most 4096 states. Each state has four Q-values in UP, LEFT, DOWN, RIGHT order. All four actions remain available; no safety filter replaces the agent's decision.

The compact state loses information. Different board situations may have the same encoding. The agent can become trapped or repeat a loop, and survival is not guaranteed.

Q-learning updates one state-action value after each training move:
Q(s, a) = Q(s, a) + alpha * (target - Q(s, a))
target = reward + gamma * max Q(next_state, next_action)

For a terminal move, target equals reward. Default alpha is 0.1 and gamma is 0.95. Unknown actions have an initial value of zero. Rewards are +20 for green, -15 for red, -0.05 for an ordinary move and -40 for death. Rewards do not use hidden distances to apples.

During training, epsilon is the probability of choosing a random action. Otherwise the agent chooses the largest Q-value, breaking ties randomly. Epsilon starts at 1, is multiplied by 0.9995 after every completed training game and has a minimum of 0.03. With -dontlearn, epsilon exploration is disabled and Q-values, learning parameters and training counters are unchanged.

The bonus interface includes the lobby, settings, a drawn board and apples, live statistics, Q-value bars, a vision overlay, results charts and exports. Reports distinguish final length from peak length and include final-length success rates for 15, 20, 25, 30 and 35.

To benchmark one unchanged model on four board sizes:
make bonuses

This runs 200 games per size and writes reports to results/bonuses. The model's SHA-256 is checked before and after evaluation. Custom settings can be used:
.venv/bin/python benchmark.py --sizes 10 15 20 30 --sessions 500 --seed 80

To watch a selected successful run on the standard board:
make bonus-demo

This uses best.json and seed 12. Final length is 40, peak length is 41 and lifetime is 372 moves. The seed is a selected reproducible example, not an estimate of random-game success. See BONUSES.md for measurements and commands.

To remove Python cache directories and .pyc or .pyo files:
make clean

To also remove the local virtual environment:
make fclean

Both commands preserve source files, trained models, reports and the original subject. They work without activating .venv. If .venv is a symbolic link, fclean removes the link rather than its target. After fclean, run make to prepare the project again. make re runs fclean followed by setup. System packages installed by setup are not uninstalled.

To install local development tools, including flake8:
make dev

To run the tests and style check:
make test
make lint

The tests cover game rules, hidden observations, Q-learning updates, model restoration, evaluation without learning, checkpoint counts, bonus statistics, lobby transitions, model reuse across board sizes and safe cleanup. Check the graphical window and controls on the campus computer before evaluation.

Run ./snake --help to see every command-line option. DEFENSE.md explains the code and questions worth understanding. models/README.md documents the supplied models. results/README.md describes report fields.

Learning reference: https://gymnasium.farama.org/v1.3.0/tutorials/training_agents/frozenlake_q_learning/
Tkinter reference: https://docs.python.org/3/library/tkinter.html

Before submission, test a fresh copy on the campus environment. Include source files, the executable snake launcher, models and documentation in the assigned Git repository. Do not commit .venv. Files are prepared locally; submission to the school repository has not been performed. Follow the campus rules on outside assistance and be able to explain the implementation.
