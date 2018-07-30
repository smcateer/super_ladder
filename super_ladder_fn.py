import pandas as pd
import re

def super_ladder(rnd_cnt=999, scale_power = 0):
    '''
    Super ladder calculator
    rnd_cnt
        - restrict the ladder to recent rounds (e.g. 5 is the last round and the 4 before it)
        - 999 to include all rounds
    scale_power
        - The scale_power tunes the effect of the opposition quality 2 ~ opposition scoring ratio^2 is used as a factor
        - the higher the factor, the more influence opposotion quality has on the ladder
        - a power of 1 means beating a 2 teams with a percentage of 50% is equal to beating 1 team with a percentage of 100%
        - a power of 2 means beating a 4 teams with a percentage of 50% is equal to beating 1 team with a percentage of 100%
    '''
    # Import data and tidy

    ## this is to d/l the data fresh
    import urllib as ul
    
    # Ladder data from https://fixturedownload.com/download/csv/afl-2018
    # url = 'https://fixturedownload.com/download/afl-2018-AUSEasternStandardTime.csv'
    # req = ul.request.urlopen(url)
    # 
    # raw = pd.read_csv(req.read(), parse_dates=['Date'])

    raw = pd.read_csv('./afl-2018-AUSEasternStandardTime.csv', parse_dates=['Date'])

    # the scores are in the format '<home_score> - <away_score>'
    def split_score(sc):
        if type(sc) == str and re.match(r'\d+ - \d+', sc):
            return sc.split(' - ')
        else:
            # For games yet to happen ... IKR right? horrible
            return [-1, -1]

    # add home and away score columns
    raw.loc[:, 'Home_score'] = raw.Result.map(lambda x: split_score(x)[0]).astype(int)
    raw.loc[:, 'Away_score'] = raw.Result.map(lambda x: split_score(x)[1]).astype(int)

    # we want to have a table of results from the perspective of each team (i.e. each game will appeaer twice)
    result_cols = ['ROUND', 'TEAM', 'VENUE', 'OPPONENT', 'SCORE', 'OPPONENT_SCORE']

    # home team results
    home_results = raw.loc[:, ['Round Number', 'Home Team', 'Location', 'Away Team', 'Home_score', 'Away_score']]
    home_results.columns = result_cols

    # away team results
    away_results = raw.loc[:, ['Round Number', 'Away Team', 'Location', 'Home Team', 'Away_score', 'Home_score']]
    away_results.columns = result_cols

    # stack 'em up
    results = pd.concat([away_results, home_results])
    # drop unplayed games
    results = results.loc[results.SCORE != -1]
    # ... and calculate the points 4 for a win, 2 for a draw
    results.loc[:, 'POINTS'] = 4*(results.SCORE > results.OPPONENT_SCORE) + 2*(results.SCORE == results.OPPONENT_SCORE)

    ### Calculate the ladder first pass

    # Calculate the standard AFL ladder

    ladder = results.loc[results.ROUND > (results.ROUND.max() - rnd_cnt)].groupby('TEAM').sum()

    ladder = ladder.loc[:, ['POINTS', 'SCORE', 'OPPONENT_SCORE']]
    ladder.loc[:, 'PERCENTAGE'] = ladder.SCORE/ladder.OPPONENT_SCORE*100
    ladder = ladder.sort_values(['POINTS', 'PERCENTAGE'], ascending=False)

    # print(ladder.reset_index())

    # Merge the results table with the percentages from the ladder
    results_up = pd.merge(results, ladder.reset_index().loc[:, ['TEAM', 'PERCENTAGE']], left_on='OPPONENT', right_on='TEAM', suffixes=('', '_JOIN'))

    ### Now we recalculate the points using opposition percentage to scale them

    # Here we scale the results by the quality of the opposition


    results_up.loc[:, 'POINTS'] = (results_up.PERCENTAGE/100)**scale_power*(4*(results_up.SCORE > results_up.OPPONENT_SCORE) + 2*(results_up.SCORE == results_up.OPPONENT_SCORE))

    # Calculate the ladder for the rounds we are interested in
    ladder_up = results_up.loc[results_up.ROUND > (results_up.ROUND.max() - rnd_cnt)].groupby('TEAM').sum()

    ladder_up = ladder_up.loc[:, ['POINTS', 'SCORE', 'OPPONENT_SCORE']]
    ladder_up.loc[:, 'PERCENTAGE'] = ladder_up.SCORE/ladder_up.OPPONENT_SCORE*100
    ladder_up = ladder_up.sort_values(['POINTS', 'PERCENTAGE'], ascending=False)

    print(ladder_up.reset_index())
