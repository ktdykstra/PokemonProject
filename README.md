# PokemonProject
Outputs from data analysis:
1. Total Games [Win + Loss]
2. Win Rate - [Win / Total Games]
3. Win Rate with individual lead - [#Hero_Lead_1∩Win / Total Games]
3. Win Rate with combined lead - [#Hero_Lead_Pair∩Win / Total Games]
4. Lose Rate against opposing individual lead - [#Villian_Lead_1∩Loss / Total Games]
5. Lose Rate against opposing combined lead - [#Villian_Lead_Pair∩Loss / Total Games]
6. Lose Rate against full team selection - [#Villian_Comp_Six∩Loss / Total Games]

## Setup

1. Create a virtual environment with `python -m venv venv`
2. Activate the virtual environment with `. venv/bin/activate`
3. Install the requirements with `pip install -r requirements.txt`
  - If you see an error with `psycopg2`, you need to install postgres locally. If you're on mac, try `brew install postgresql`.
