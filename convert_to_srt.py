import pandas as pd

def get_overlay(csv_loc, name):
    column_names = ['start', 'start_ms', 'end', 'end_ms', 'overs', 'run', 'bowler', 'batter']  ### , 'commentary'
    df = pd.read_csv(name)
    counter = 1
    with open(csv_loc + "output.srt", 'w') as file:
        for index, row in df.iterrows():
            milli1 = str(row['start_ms']).split(".")[0].replace("nan", "000")
            milli2 = str(row['end_ms']).split(".")[0].replace("nan", "000")
            print("%d\n%s,%s --> %s,%s\nOver: %s\nRun: %s\nBowler: %s\nBatter: %s\n" % (
                counter, row['start'], milli1, row['end'], milli2, row['overs'], row['run'], row['bowler'], row['batter']), file=file)  ## row['commentary']
            counter += 1