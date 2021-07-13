from SolarInfo import app
from apscheduler.schedulers.background import BackgroundScheduler 

if __name__ == '__main__':
    app.run(debug=True)
    scheduler = BackgroundScheduler()
    scheduler.add_job(parse_func, 'interval', seconds=10)
    scheduler.start()
    app.run(debug=True)