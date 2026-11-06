The supplied models use JSON format version 1 and state encoding rays-12bits-v1. They contain a Q-table, learning parameters, counters and the agent's random generator state. No Q-values are hardcoded before training.

1sessions.json was trained for 1 completed game.
10sessions.json was trained for 10 completed games.
100sessions.json was trained for 100 completed games.
candidate.json was trained for 30000 completed games.
100000sessions.json was trained for 100000 completed games.
best.json is a copy of 100000sessions.json.

The models were trained from the project directory using Python 3.14.5 and default parameters:
./snake -visual off --quiet -sessions 30000 --seed 42 --checkpoint-dir models -save models/candidate.json --report results/training.json
./snake -visual off --quiet -load models/candidate.json -sessions 70000 --seed 123 -save models/100000sessions.json --report results/training-continued.json

The first command creates the 1, 10 and 100 game checkpoints. The second adds 70000 games. best.json was selected by mean final length on 200 evaluation games with seed 2026: 22.030 for the 100000-game model versus 20.835 for the 30000-game model.

Each model was evaluated without learning on a 10 by 10 board, for 200 games with seed 2026 and a 3000-move limit.

After 1 training game, mean final length was 3.010, mean lifetime was 3.760 moves and final length reached 10 in 0% of games.
After 10 training games, mean final length was 3.065, mean lifetime was 4.440 moves and final length reached 10 in 0% of games.
After 100 training games, mean final length was 3.190, mean lifetime was 220.035 moves and final length reached 10 in 0% of games.
After 30000 training games, mean final length was 20.835, mean lifetime was 571.430 moves and final length reached 10 in 91.0% of games.
After 100000 training games, mean final length was 22.030, mean lifetime was 540.655 moves and final length reached 10 in 88.5% of games.

Improving one metric does not necessarily improve every other metric. The 100-game model often loops: 14 of its 200 evaluation games reached the step limit. This explains its relatively long lifetime despite low final length.

To compare a model, replace FILE with its name:
./snake -visual off --quiet -load models/FILE.json -dontlearn -sessions 200 --seed 2026 --report results/FILE-evaluation.json

After model selection, best.json was evaluated on a separate set of 1000 games with seed 2027:
./snake -visual off --quiet -load models/best.json -dontlearn -sessions 1000 --seed 2027 --report results/best-held-out.json --csv results/best-held-out.csv

Mean final length was 22.847. Mean peak length was 22.928. Final length was at least 10 in 92.8% of games. The largest peak length was 54. Mean lifetime was 389.29 moves. The step limit ended 73 of 1000 games. Limited games count as 3000 moves in these statistics.

The same model was also evaluated on a 15 by 15 board for 100 games with seed 2027. Mean final length was 34.84, peak length reached 61 and 95% of games ended with length at least 10. The report is results/size15.json.

These are measurements of particular runs, not guarantees for every game. Always use -dontlearn when comparing saved models. Otherwise the loaded agent continues learning in memory. Neither make clean nor make fclean deletes models.
