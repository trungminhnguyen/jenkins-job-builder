def monkey_patch():
    import jenkins
    from jenkins import (JenkinsException, NotFoundException, TimeoutException,
                         EmptyResponseException)
    import socket
    from jenkins_jobs import urllib_kerb
    from six.moves.urllib.error import HTTPError, URLError
    from six.moves.urllib.request import build_opener

    # copy paste of jenkins.Jenkins.jenkins_open
    #  only adding HTTPNegotiateHandler urllib handler
    def _jenkins_open(self, req, add_crumb=True):
        '''Utility routine for opening an HTTP request to a Jenkins server.

        This should only be used to extends the :class:`Jenkins` API.
        '''
        try:
            if self.auth:
                req.add_header('Authorization', self.auth)
            if add_crumb:
                self.maybe_add_crumb(req)
            opener = build_opener()
            opener.add_handler(urllib_kerb.HTTPNegotiateHandler())
            response = opener.open(req, timeout=self.timeout).read()
            if response is None:
                raise EmptyResponseException(
                    "Error communicating with server[%s]: "
                    "empty response" % self.server)
            return response.decode('utf-8')
        except HTTPError as e:
            # Jenkins's funky authentication means its nigh impossible to
            # distinguish errors.
            if e.code in [401, 403, 500]:
                # six.moves.urllib.error.HTTPError provides a 'reason'
                # attribute for all python version except for ver 2.6
                # Falling back to HTTPError.msg since it contains the
                # same info as reason
                raise JenkinsException(
                    'Error in request. ' +
                    'Possibly authentication failed [%s]: %s' % (
                        e.code, e.msg)
                )
            elif e.code == 404:
                raise NotFoundException('Requested item could not be found')
            else:
                raise
        except socket.timeout as e:
            raise TimeoutException('Error in request: %s' % (e))
        except URLError as e:
            # python 2.6 compatibility to ensure same exception raised
            # since URLError wraps a socket timeout on python 2.6.
            if str(e.reason) == "timed out":
                raise TimeoutException('Error in request: %s' % (e.reason))
            raise JenkinsException('Error in request: %s' % (e.reason))
    jenkins.Jenkins.jenkins_open = _jenkins_open

try:
    import kerberos
    assert kerberos  # pyflakes
    monkey_patch()
except ImportError:
    pass
