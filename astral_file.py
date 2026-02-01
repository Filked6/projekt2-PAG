def determine_day_night(row, sun_schedule):
    d_date = row['Data'].date()
    d_time = row['Data']  #Pełen timestamp

    schedule = sun_schedule.get(d_date)
    if not schedule or not schedule['sunrise']:
        return "Nieokreślony"

    if schedule['sunrise'] <= d_time < schedule['sunset']:
        return "Dzień"
    else:
        return "Noc"