from celery import shared_task, Task
from tornado.options import define, options

import mltshpoptions


class MltshpTask(Task):

    def delay_or_run(self, *args, **kwargs):
        if not options.use_workers:
            self(*args, **kwargs)
            return
        try:
            asyncresult = self.delay(*args, **kwargs)
        except Exception:
            self(*args, **kwargs)

            #if options.postmark_api_key and not options.debug_workers:
            #    pm = postmark.PMMail(api_key=options.postmark_api_key,
            #            sender="hello@mltshp.com", to="alerts@mltshp.com",
            #            subject="ALERT!!! RABBITMQ IS DOWN",
            #            text_body="WTF.")
            #    pm.send()
        else:
            if options.debug_workers:
                asyncresult.get()


def mltshp_task(*args, **options):
    # This is how celery's periodic_task decorator customizes the class, so try it here too.
    return shared_task(**dict({"base": MltshpTask}, **options))
