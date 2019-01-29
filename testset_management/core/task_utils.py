import json
import boto3

from django.conf import settings
from zappa.async import AsyncException, LambdaAsyncResponse, get_func_task_path, update_wrapper


AWS_LAMBDA_FUNCTION_NAME = 'zappa-handwritten-testset-manager-prod'


def get_boto_session():
    return boto3.session.Session(region_name='ap-northeast-2',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)


# Code reference : https://github.com/Miserlou/Zappa/blob/master/zappa/async.py

# Modifed version of zappa.async.LambdaAsyncResponse
class CustomLambdaAsyncResponse(LambdaAsyncResponse):
    def __init__(self):
        self.client = get_boto_session().client('lambda')

    def _send(self, message):
        """
        Given a message, directly invoke the lamdba function for this task.
        """
        message['command'] = 'zappa.async.route_lambda_task'
        payload = json.dumps(message).encode('utf-8')
        if len(payload) > 128000: # pragma: no cover
            raise AsyncException("Payload too large for async Lambda call")
        self.response = self.client.invoke(
                                    FunctionName=AWS_LAMBDA_FUNCTION_NAME,
                                    InvocationType='Event',
                                    Payload=payload
                                )
        self.sent = (self.response.get('StatusCode', 0) == 202)


# Modifed version of zappa.async.task
def lambda_task(func):
    """
    Decorator to make function run under zappa environment.
    Args:
        func (function): the function to be wrapped
    Further requirements:
        - func must be an independent top-level function.
            i.e. not a class method or an anonymous function
        - args & kwargs must be serializable
    Usage:
        @lambda_task
        def render(question_id):
            question.render()
        # You can call above function wherever you want;
        render(question_id=1)
        # and zappa task (which is actually AWS lambda function) will be invoked.
    """
    task_path = get_func_task_path(func)
    
    def _run_async(*args, **kwargs):
        """
        This is the wrapping async function that replaces the decorated function.
        Returns:
            The object returned includes state of the dispatch.
        """
        send_result = CustomLambdaAsyncResponse().send(task_path, args, kwargs)
        return send_result
    
    update_wrapper(_run_async, func)
    
    _run_async.service = 'lambda'
    _run_async.sync = func
    
    return _run_async
