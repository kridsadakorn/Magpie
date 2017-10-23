from pyramid.httpexceptions import *
from sys import exc_info
import types

# control variables to avoid infinite recursion in case of
# major programming error to avoid application hanging
RAISE_RECURSIVE_SAFEGUARD_MAX = 5
RAISE_RECURSIVE_SAFEGUARD_COUNT = 0


def verify_param(param, paramCompare=None, httpError=HTTPNotAcceptable, msgOnFail="", contentType='application/json',
                 notNone=False, notEmpty=False, notIn=False, isNone=False, isEmpty=False, isIn=False, ofType=None):
    """
    Evaluate various parameter combinations given the requested flags.
    Given a failing verification, directly raises the specified `httpError`.
    Invalid exceptions generated by this verification process are treated as `HTTPInternalServerError`.
    Exceptions are generated using the standard output method.

    :param param: (bool) parameter value to evaluate
    :param paramCompare:
        other value(s) to test against, can be an iterable (single value resolved as iterable unless None)
        to test for None type, use `isNone`/`notNone` flags instead or `paramCompare`=[None]
    :param httpError: (HTTPError) derived exception to raise on test failure (default: `HTTPNotAcceptable`)
    :param msgOnFail: (str) message details to return in HTTP exception if flag condition failed
    :param contentType: format in which to return the exception ('application/json', 'text/html' or 'text/plain')
    :param notNone: (bool) test that `param` is None type
    :param notEmpty: (bool) test that `param` is an empty string
    :param notIn: (bool) test that `param` does not exist in `paramCompare` values
    :param isNone: (bool) test that `param` is None type
    :param isEmpty: (bool) test `param` for an empty string
    :param isIn: (bool) test that `param` exists in `paramCompare` values
    :param ofType: (type) test that `param` is of same type as specified type by `ofType` (except NoneType)
    :raises `HTTPError`: if tests fail, specified exception is raised (default: `HTTPNotAcceptable`)
    :raises `HTTPInternalServerError`: for evaluation error
    :return: nothing if all tests passed
    """
    # precondition evaluation of input parameters
    try:
        if type(notNone) is not bool:
            raise Exception("`notNone` is not a `bool`")
        if type(notEmpty) is not bool:
            raise Exception("`notEmpty` is not a `bool`")
        if type(notIn) is not bool:
            raise Exception("`notIn` is not a `bool`")
        if type(isNone) is not bool:
            raise Exception("`isNone` is not a `bool`")
        if type(isEmpty) is not bool:
            raise Exception("`isEmpty` is not a `bool`")
        if type(isIn) is not bool:
            raise Exception("`isIn` is not a `bool`")
        if paramCompare is None and (isIn or notIn):
            raise Exception("`paramCompare` cannot be `None` with specified test flags")
        if not hasattr(paramCompare, '__iter__'):
            paramCompare = [paramCompare]
    except Exception as e:
        raise_http(httpError=HTTPInternalServerError, detail=repr(e),
                   content={'traceback': repr(exc_info())}, contentType=contentType)

    # evaluate requested parameter combinations
    status = False
    if notNone:
        status = status or (param is None)
    if isNone:
        status = status or (param is not None)
    if notEmpty:
        status = status or (param == "")
    if isEmpty:
        status = status or (not param == "")
    if notIn:
        status = status or (param in paramCompare)
    if isIn:
        status = status or (param not in paramCompare)
    if ofType is not None:
        status = status or (not type(param) == ofType)
    if status:
        raise_http(httpError, detail=msgOnFail, content={'param': repr(param)}, contentType=contentType)


def evaluate_call(call, fallback=None, httpError=HTTPInternalServerError, msgOnFail="",
                  content=None, contentType='application/json'):
    """
    Evaluates the specified `call` with a wrapped HTTP exception handling.
    On failure, tries to call `fallback` if specified, and finally raises the specified `httpError`.
    Any potential error generated by `fallback` or `httpError` themselves are treated as `HTTPInternalServerError`.
    Exceptions are generated using the standard output method formatted based on the specified `contentType`.

    Example:
        normal call:
            ```
            try:
                res = func(args)
            except Exception as e:
                fb_func()
                raise HTTPExcept(e.message)
            ```
        wrapped call:
            ```
            res = evaluate_call(lambda: func(args), fallback=lambda: fb_func(), httpError=HTTPExcept, msgOnFail="...")
            ```

    :param call: function to call, *MUST* be specified as `lambda: <function_call>`
    :param fallback: function to call (if any) when `call` failed, *MUST* be `lambda: <function_call>`
    :param httpError: (HTTPError) alternative exception to raise on `call` failure
    :param msgOnFail: (str) message details to return in HTTP exception if `call` failed
    :param content: json formatted additional content to provide in case of exception
    :param contentType: format in which to return the exception ('application/json', 'text/html' or 'text/plain')
    :raises httpError: on `call` failure
    :raises `HTTPInternalServerError`: on `fallback` failure
    :return: whichever return value `call` might have if no exception occurred
    """
    msgOnFail = repr(msgOnFail) if type(msgOnFail) is not str else msgOnFail
    if not islambda(call):
        raise_http(httpError=HTTPInternalServerError,
                   detail="Input `call` is not a lambda expression",
                   content={'call': {'detail': msgOnFail, 'content': repr(content)}},
                   contentType=contentType)

    # preemptively check fallback to avoid possible call exception without valid recovery
    if fallback is not None:
        if not islambda(fallback):
            raise_http(httpError=HTTPInternalServerError,
                       detail="Input `fallback`  is not a lambda expression, not attempting `call`",
                       content={'call': {'detail': msgOnFail, 'content': repr(content)}},
                       contentType=contentType)
    try:
        return call()
    except Exception as e:
        ce = repr(e)
    try:
        if fallback is not None:
            fallback()
    except Exception as e:
        fe = repr(e)
        raise_http(httpError=HTTPInternalServerError,
                   detail="Exception occurred during `fallback` called after failing `call` exception",
                   content={'call': {'exception': ce, 'detail': msgOnFail, 'content': repr(content)},
                            'fallback': {'exception': fe}},
                   contentType=contentType)
    raise_http(httpError, detail=msgOnFail,
               content={'call': {'exception': ce, 'content': repr(content)}},
               contentType=contentType)


def valid_http(httpSuccess=HTTPOk, detail="", content=None, contentType='application/json'):
    """
    Returns successful HTTP with standardized information formatted with content type.
    (see `valid_http` for HTTP error calls)

    :param httpSuccess: any derived class from base `HTTPSuccessful` (default: HTTPOk)
    :param detail: additional message information (default: empty)
    :param content: json formatted content to include
    :param contentType: format in which to return the exception ('application/json', 'text/html' or 'text/plain')
    :return `HTTPSuccessful`: formatted successful with additional details and HTTP code
    """
    content = dict() if content is None else content
    detail = repr(detail) if type(detail) is not str else detail
    httpCode, detail, content = validate_params(httpSuccess, HTTPSuccessful, detail, content, contentType)
    json_body = format_content_json_str(httpCode, detail, content, contentType)
    return output_http_format(httpSuccess, json_body, outputType=contentType, outputMode='return')


def raise_http(httpError=HTTPInternalServerError, detail="", content=None, contentType='application/json'):
    """
    Raises error HTTP with standardized information formatted with content type.
    (see `valid_http` for HTTP successful calls)

    The content contains the corresponding http error code, the provided message as detail and
    optional specified additional json content (kwarg dict).

    :param httpError: any derived class from base `HTTPError` (default: HTTPInternalServerError)
    :param detail: additional message information (default: empty)
    :param content: json formatted content to include
    :param contentType: format in which to return the exception ('application/json', 'text/html' or 'text/plain')
    :raises `HTTPError`: formatted raised exception with additional details and HTTP code
    """
    # fail-fast if recursion generates too many calls
    # this would happen only if a major programming error occurred within this function
    global RAISE_RECURSIVE_SAFEGUARD_MAX
    global RAISE_RECURSIVE_SAFEGUARD_COUNT
    RAISE_RECURSIVE_SAFEGUARD_COUNT = RAISE_RECURSIVE_SAFEGUARD_COUNT + 1
    if RAISE_RECURSIVE_SAFEGUARD_COUNT > RAISE_RECURSIVE_SAFEGUARD_MAX:
        raise HTTPInternalServerError(detail="Terminated. Too many recursions of `raise_http`")

    # try dumping content with json format, `HTTPInternalServerError` with caller info if fails.
    # content is added manually to avoid auto-format and suppression of fields by `HTTPException`
    httpCode, detail, content = validate_params(httpError, HTTPError, detail, content, contentType)
    json_body = format_content_json_str(httpError.code, detail, content, contentType)
    output_http_format(httpError, json_body, outputType=contentType, outputMode='raise')


def validate_params(httpClass, httpBase, detail, content, contentType):
    """
    Validates parameter types and formats required by `valid_http` and `raise_http`.

    :raise `HTTPInternalServerError`: if any parameter is of invalid expected format
    :returns httpCode, detail, content: parameters with corrected and validated format if applicable
    """
    # verify input arguments, raise `HTTPInternalServerError` with caller info if invalid
    # cannot be done within a try/except because it would always trigger with `raise_http`
    content = dict() if content is None else content
    detail = repr(detail) if type(detail) is not str else detail
    if not isclass(httpClass):
        raise_http(httpError=HTTPInternalServerError,
                   detail="Object specified is not of type `HTTPError`",
                   contentType='application/json',
                   content={'caller': {'content': content,
                                       'detail': detail,
                                       'code': 520,  #'unknown' error
                                       'type': contentType}})
    # if `httpClass` derives from `httpBase` (ex: `HTTPSuccessful` or `HTTPError`) it is of proper requested type
    # if it derives from `HTTPException`, it *could* be different than base (ex: 2xx instead of 4xx codes)
    # return 'unknown error' (520) if not of lowest level base `HTTPException`, otherwise use the available code
    httpCode = httpClass.code if issubclass(httpClass, httpBase) else \
               httpClass.code if issubclass(httpClass, HTTPException) else 520
    if not issubclass(httpClass, httpBase):
        raise_http(httpError=HTTPInternalServerError,
                   detail="Invalid `httpBase` derived class specified",
                   contentType='application/json',
                   content={'caller': {'content': content,
                                       'detail': detail,
                                       'code': httpCode,
                                       'type': contentType}})
    if contentType not in ['application/json', 'text/html', 'text/plain']:
        raise_http(httpError=HTTPInternalServerError,
                   detail="Invalid `contentType` specified for exception output",
                   contentType='application/json',
                   content={'caller': {'content': content,
                                       'detail': detail,
                                       'code': httpCode,
                                       'type': contentType}})
    return httpCode, detail, content


def format_content_json_str(httpCode, detail, content, contentType):
    """
    Inserts the code, details, content and type within the body using json format.
    Includes also any other specified json formatted content in the body.
    Returns the whole json body as a single string for output.

    :raise `HTTPInternalServerError`: if parsing of the json content failed
    :returns: formatted json content as string with added HTTP code and details
    """
    json_body = {}
    try:
        content['code'] = httpCode
        content['detail'] = detail
        content['type'] = contentType
        json_body = json.dumps(content)
    except Exception as e:
        msg = "Dumping json content [" + str(content) + \
              "] resulted in exception [" + repr(e) + "]"
        raise_http(httpError=HTTPInternalServerError, detail=msg,
                   contentType='application/json',
                   content={'traceback': repr(exc_info()),
                            'caller': {'content': repr(content),   # raw string to avoid recursive json.dumps error
                                       'detail': detail,
                                       'code': httpCode,
                                       'type': contentType}})
    return json_body


def output_http_format(httpClass, jsonContent, outputType='text/plain', outputMode='raise'):
    """
    Formats the HTTP response output according to desired `outputType` using provided HTTP code and content.

    :param httpClass: HTTPException derived class to use for output (code, generic title/explanation, etc.)
    :param jsonContent: (str) formatted json content providing additional details for the response cause
    :param outputType: {'application/json','text/html','text/plain'} (default: 'text/plain')
    :param outputMode: {'raise','return'} (default: 'raise')
    :return: modified HTTPException derived class with information and output type if `outputMode` is 'return'
    :raises: modified HTTPException derived class with information and output type if `outputMode` is 'raise'
    """
    # content body is added manually to avoid auto-format and suppression of fields by `HTTPException`
    jsonContent = str(jsonContent) if not type(jsonContent) == str else jsonContent

    # directly output json if asked with 'application/json'
    if outputType == 'application/json':
        if outputMode == 'return':
            return httpClass(body=jsonContent, content_type='application/json')
        raise httpClass(body=jsonContent, content_type='application/json')

    # otherwise json is contained within the html <body> section
    if outputType == 'text/html':
        # add preformat <pre> section to output as is within the <body> section
        htmlBody = httpClass.explanation + "<br><h2>Exception Details</h2>" + \
                   "<pre style='word-wrap: break-word; white-space: pre-wrap;'>" + \
                   jsonContent + "</pre>"
        if outputMode == 'return':
            return httpClass(body_template=htmlBody, content_type='text/html')
        raise httpClass(body_template=htmlBody, content_type='text/html')

    # default back to 'text/plain'
    if outputMode == 'return':
        return httpClass(body=jsonContent, content_type='text/plain')
    raise httpClass(body=jsonContent, content_type='text/plain')


def islambda(func):
    return isinstance(func, types.LambdaType) and func.__name__ == (lambda: None).__name__


def isclass(obj):
    """
    Evaluate an object for class type (ie: class definition, not an instance nor any other type).

    :param obj: object to evaluate for class type
    :return: (bool) indicating if `object` is a class
    """
    return isinstance(obj, (type, types.ClassType))
