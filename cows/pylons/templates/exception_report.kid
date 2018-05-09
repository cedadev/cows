<?xml version="1.0" encoding="UTF-8"?>
<?python
"""
A OWS exception report.

@param report: An ows_common.exception_report object
"""

def hide_optionals(attrDict, optionals=None):
    """
    Returns a copy of attrDict where any value which is None and in optionals is removed.

    If optionals=None all keys are considered optional.

    @todo: move this to a utils module
    """
    od = {}
    for key, value in attrDict.items():
        if (value is not None) or (optionals and key not in optionals):
            od[key] = value

    return od
?>
<ExceptionReport xmlns="http://www.opengis.net/ows"
		 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
		 xmlns:py="http://purl.org/kid/ns#"
		 xsi:schemaLocation="http://www.opengis.net/ows owsExceptionReport.xsd"
		 version="${report.version}"
                 py:attrs="hide_optionals(dict(language=report.lang))">
<Exception py:for="e in report.exceptions"
	   py:content="e.text"
	   exceptionCode="${e.code}"
	   py:attrs="hide_optionals(dict(locator=e.locator))"/>
</ExceptionReport>
                 