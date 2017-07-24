import logging
import sys
import inspect
from digcollretriever_lib.exceptions import MutuallyExclusiveParametersError
from digcollretriever_lib.storageinterfaces import *

log = logging.getLogger(__name__)


def sane_transform_args(args, o_width, o_height):
    # Scale and width/height are mutually exclusive
    if (args['height'] or args['width']) and args['scale']:
        log.warn(
            "Received a request containing scale in conjuction with width or height"
        )
        raise MutuallyExclusiveParametersError(
            "Scale can not be used in conjunction with width or height"
        )
    # If height or width is omitted use the original
    if args['height'] or args['width']:
        if args['height'] and not args['width']:
            args['width'] = o_width
            log.debug("Assuming width as default")
        if args['width'] and not args['height']:
            args['height'] = o_height
            log.debug("Assuming height as default")
    # Quality for jpgs only goes to 95. See Pillow docs
    # and talk about jpg compression
    try:
        if args['quality'] is not None:
            if args['quality'] > 95:
                args['quality'] = 95
                log.info("Quality > 95 passed. Capping value")
        else:
            args['quality'] = 95
    except KeyError:
        pass
    # Lets all agree to never make something twice as big
    # as the original is, okay? Good.
    if args['height'] is not None:
        if args['height'] > (2 * o_height):
            args['height'] = 2 * o_height
            log.info("Height > 2 * original passed. Capping value")
    if args['width'] is not None:
        if args['width'] > (2 * o_width):
            args['width'] = 2 * o_width
            log.info("Width > 2 * original passed. Capping value")
    if args['scale'] is not None:
        if args['scale'] > 2:
            args['scale'] = 2
            log.info("Scale > 2 passed. Capping value")
    # And how about we but some bottom bounds on here to,
    # say dimensions no lower than 10x10 and scaling no lower
    # than 1%
    if args['width'] is not None:
        if args['width'] < 10:
            args['width'] = 10
            log.info("Width < 10 passed. Capping value")
    if args['height'] is not None:
        if args['height'] < 10:
            args['height'] = 10
            log.info("Height < 10 passed. Capping value")
    if args['scale'] is not None:
        if args['scale'] < .01:
            args['scale'] = .01
            log.info("Scale < .01 passed. Capping value")
    return args


def determine_identifier_type(identifier):
    id_types = [
        x[1] for x in inspect.getmembers(
            sys.modules['digcollretriever_lib.storageinterfaces'],
            inspect.isclass
        )
    ]

    for x in id_types:
        if x.claim_identifier(identifier):
            return x
    raise UnknownIdentifierFormatError()
