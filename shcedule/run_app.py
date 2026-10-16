import schedule
import time
import threading
import model_api.CppApi
class run_app :
    def my_job():
        print("Job is running...")
        # data={
        #     "month":12,
        #     "year":2023,
        #     "company":""
        # }
        #Type Post Payement
        model_api.CppApi.extractDataPay('')#call function eventPay
        # model_api.CppApi.commissionBatch(data)
        
    # Schedule the job to run every 1 minute
    
    # schedule.every(5).seconds.do(my_job)

    while True:
        schedule.run_pending()
        time.sleep(1)
     