""":mod:`wand.image` --- Image objects
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Opens and manipulates images. Image objects can be used in :keyword:`with`
statement, and these resources will be automatically managed (even if any
error happened)::

    with Image(filename='pikachu.png') as i:
        print('width =', i.width)
        print('height =', i.height)

"""
import ctypes
import functools
import numbers
import weakref

from . import assertions
from .api import libc, libmagick, library
from .color import Color
from .compat import (abc, binary, binary_type, encode_filename, file_types,
                     PY3, string_type, text, xrange)
from .exceptions import (MissingDelegateError, WandException,
                         WandRuntimeError, WandLibraryVersionError)
from .font import Font
from .resource import DestroyedResourceError, Resource
from .cdefs.structures import (CCObjectInfo, ChannelFeature, GeomertyInfo,
                               PixelInfo, RectangleInfo)
from .version import MAGICK_VERSION_NUMBER, MAGICK_HDRI


__all__ = ('ALPHA_CHANNEL_TYPES', 'AUTO_THRESHOLD_METHODS', 'CHANNELS',
           'COLORSPACE_TYPES', 'COMPARE_METRICS', 'COMPOSITE_OPERATORS',
           'COMPRESSION_TYPES', 'DISPOSE_TYPES', 'DISTORTION_METHODS',
           'DITHER_METHODS', 'EVALUATE_OPS', 'FILTER_TYPES', 'FUNCTION_TYPES',
           'GRAVITY_TYPES', 'IMAGE_LAYER_METHOD', 'IMAGE_TYPES',
           'INTERLACE_TYPES', 'KERNEL_INFO_TYPES', 'MORPHOLOGY_METHODS',
           'NOISE_TYPES', 'ORIENTATION_TYPES', 'PIXEL_INTERPOLATE_METHODS',
           'RENDERING_INTENT_TYPES', 'SPARSE_COLOR_METHODS', 'STATISTIC_TYPES',
           'STORAGE_TYPES', 'VIRTUAL_PIXEL_METHOD', 'UNIT_TYPES',
           'BaseImage', 'ChannelDepthDict', 'ChannelImageDict',
           'ClosedImageError', 'HistogramDict', 'Image', 'ImageProperty',
           'Iterator', 'Metadata', 'OptionDict', 'manipulative',
           'ArtifactTree', 'ProfileDict', 'ConnectedComponentObject')


#: (:class:`tuple`) The list of :attr:`~wand.image.BaseImage.alpha_channel`
#: types.
#:
#: - ``'undefined'``
#: - ``'activate'``
#: - ``'background'``
#: - ``'copy'``
#: - ``'deactivate'``
#: - ``'discrete'`` - Only available in ImageMagick-7
#: - ``'extract'``
#: - ``'off'`` - Only available in ImageMagick-7
#: - ``'on'`` - Only available in ImageMagick-7
#: - ``'opaque'``
#: - ``'reset'`` - Only available in ImageMagick-6
#: - ``'set'``
#: - ``'shape'``
#: - ``'transparent'``
#: - ``'flatten'`` - Only available in ImageMagick-6
#: - ``'remove'``
#:
#: .. seealso::
#:    `ImageMagick Image Channel`__
#:       Describes the SetImageAlphaChannel method which can be used
#:       to modify alpha channel. Also describes AlphaChannelType
#:
#:    __ http://www.imagemagick.org/api/channel.php#SetImageAlphaChannel
ALPHA_CHANNEL_TYPES = ('undefined', 'activate', 'background', 'copy',
                       'deactivate', 'extract', 'opaque', 'reset', 'set',
                       'shape', 'transparent', 'flatten', 'remove',
                       'associate', 'disassociate')
if MAGICK_VERSION_NUMBER >= 0x700:  # pragma: no cover
    ALPHA_CHANNEL_TYPES = ('undefined', 'activate', 'associate', 'background',
                           'copy', 'deactivate', 'discrete', 'disassociate',
                           'extract', 'off', 'on', 'opaque', 'remove', 'set',
                           'shape', 'transparent')


#: (:class:`tuple`) The list of methods used by
#: :meth:`Image.auto_threshold() <wand.image.BaseImage.auto_threshold>`
#:
#: - ``'undefined'``
#: - ``'kapur'``
#: - ``'otsu'``
#: - ``'triangle'``
#:
#: .. versionadded:: 0.5.5
AUTO_THRESHOLD_METHODS = ('undefined', 'kapur', 'otsu', 'triangle')


#: (:class:`dict`) The dictionary of channel types.
#:
#: - ``'undefined'``
#: - ``'red'``
#: - ``'gray'``
#: - ``'cyan'``
#: - ``'green'``
#: - ``'magenta'``
#: - ``'blue'``
#: - ``'yellow'``
#: - ``'alpha'``
#: - ``'opacity'``
#: - ``'black'``
#: - ``'index'``
#: - ``'composite_channels'``
#: - ``'all_channels'``
#: - ``'sync_channels'``
#: - ``'default_channels'``
#:
#: .. seealso::
#:
#:    `ImageMagick Color Channels`__
#:       Lists the various channel types with descriptions of each
#:
#:    __ http://www.imagemagick.org/Magick++/Enumerations.html#ChannelType
#:
#: .. versionchanged:: 0.5.5
#:    Deprecated ``true_alpha``, ``rgb_channels``, and ``gray_channels``
#:    values in favor of MagickCore channel parser.
#:
CHANNELS = dict(undefined=0, red=1, gray=1, cyan=1, green=2, magenta=2,
                blue=4, yellow=4, alpha=8, opacity=8, black=32, index=32,
                composite_channels=47, all_channels=134217727, true_alpha=64,
                rgb=7, rgb_channels=7, gray_channels=1, sync_channels=256,
                default_channels=134217719)
if MAGICK_VERSION_NUMBER >= 0x700:  # pragma: no cover
    CHANNELS = dict(undefined=0, red=1, gray=1, cyan=1, green=2, magenta=2,
                    blue=4, yellow=4, black=8, alpha=16, opacity=16, index=32,
                    readmask=0x0040, write_mask=128, meta=256,
                    composite_channels=31, all_channels=134217727,
                    true_alpha=256, rgb=7, rgb_channels=7, gray_channels=1,
                    sync_channels=131072, default_channels=134217727)


#: (:class:`tuple`) The list of colorspaces.
#:
#: - ``'undefined'``
#: - ``'rgb'``
#: - ``'gray'``
#: - ``'transparent'``
#: - ``'ohta'``
#: - ``'lab'``
#: - ``'xyz'``
#: - ``'ycbcr'``
#: - ``'ycc'``
#: - ``'yiq'``
#: - ``'ypbpr'``
#: - ``'yuv'``
#: - ``'cmyk'``
#: - ``'srgb'``
#: - ``'hsb'``
#: - ``'hsl'``
#: - ``'hwb'``
#: - ``'rec601luma'`` - Only available with ImageMagick-6
#: - ``'rec601ycbcr'``
#: - ``'rec709luma'`` - Only available with ImageMagick-6
#: - ``'rec709ycbcr'``
#: - ``'log'``
#: - ``'cmy'``
#: - ``'luv'``
#: - ``'hcl'``
#: - ``'lch'``
#: - ``'lms'``
#: - ``'lchab'``
#: - ``'lchuv'``
#: - ``'scrgb'``
#: - ``'hsi'``
#: - ``'hsv'``
#: - ``'hclp'``
#: - ``'xyy'`` - Only available with ImageMagick-7
#: - ``'ydbdr'``
#:
#: .. seealso::
#:
#:    `ImageMagick Color Management`__
#:       Describes the ImageMagick color management operations
#:
#:    __ http://www.imagemagick.org/script/color-management.php
#:
#: .. versionadded:: 0.3.4
COLORSPACE_TYPES = ('undefined', 'rgb', 'gray', 'transparent', 'ohta', 'lab',
                    'xyz', 'ycbcr', 'ycc', 'yiq', 'ypbpr', 'yuv', 'cmyk',
                    'srgb', 'hsb', 'hsl', 'hwb', 'rec601luma', 'rec601ycbcr',
                    'rec709luma', 'rec709ycbcr', 'log', 'cmy', 'luv', 'hcl',
                    'lch', 'lms', 'lchab', 'lchuv', 'scrgb', 'hsi', 'hsv',
                    'hclp', 'ydbdr')
if MAGICK_VERSION_NUMBER >= 0x700:  # pragma: no cover
    COLORSPACE_TYPES = ('undefined', 'cmy', 'cmyk', 'gray', 'hcl', 'hclp',
                        'hsb', 'hsi', 'hsl', 'hsv', 'hwb', 'lab', 'lch',
                        'lchab', 'lchuv', 'log', 'lms', 'luv', 'ohta',
                        'rec601ycbcr', 'rec709ycbcr', 'rgb', 'scrgb', 'srgb',
                        'transparent', 'xyy', 'xyz', 'ycbcr', 'ycc', 'ydbdr',
                        'yiq', 'ypbpr', 'yuv')

#: (:class:`tuple`) The list of compare metric types used by
#: :meth:`Image.compare() <wand.image.BaseImage.compare>` and
#: :meth:`Image.similarity() <wand.image.BaseImage.similarity>` methods.
#:
#: - ``'undefined'``
#: - ``'absolute'``
#: - ``'fuzz'``
#: - ``'mean_absolute'``
#: - ``'mean_error_per_pixel'``
#: - ``'mean_squared'``
#: - ``'normalized_cross_correlation'``
#: - ``'peak_absolute'``
#: - ``'peak_signal_to_noise_ratio'``
#: - ``'perceptual_hash'`` - Available with ImageMagick-7
#: - ``'root_mean_square'``
#: - ``'structural_similarity'`` - Available with ImageMagick-7
#: - ``'structural_dissimilarity'`` - Available with ImageMagick-7
#:
#: .. seealso::
#:
#:    `ImageMagick Compare Operations`__
#:
#:    __ http://www.imagemagick.org/Usage/compare/
#:
#: .. versionadded:: 0.4.3
#:
#: .. versionchanged:: 0.5.4 - Remapped :c:data:`MetricType` enum.
COMPARE_METRICS = ('undefined', 'absolute',
                   'mean_absolute', 'mean_error_per_pixel',
                   'mean_squared', 'peak_absolute',
                   'peak_signal_to_noise_ratio', 'root_mean_square',
                   'normalized_cross_correlation', 'fuzz')
if MAGICK_VERSION_NUMBER >= 0x700:  # pragma: no cover
    COMPARE_METRICS = ('undefined', 'absolute', 'fuzz', 'mean_absolute',
                       'mean_error_per_pixel', 'mean_squared',
                       'normalized_cross_correlation', 'peak_absolute',
                       'peak_signal_to_noise_ratio', 'perceptual_hash',
                       'root_mean_square', 'structural_similarity',
                       'structural_dissimilarity')


#: (:class:`tuple`) The list of complext operators used by
#: :meth:`Image.complex() <wand.image.BaseImage.complex>`.
#:
#: - ``'undefined'``
#: - ``'add'``
#: - ``'conjugate'``
#: - ``'divide'``
#: - ``'magnitude',``
#: - ``'multiply'``
#: - ``'real_imaginary'``
#: - ``'subtract'``
#:
#: .. versionadded:: 0.5.5
COMPLEX_OPERATORS = ('undefined', 'add', 'conjugate', 'divide', 'magnitude',
                     'multiply', 'real_imaginary', 'subtract')


#: (:class:`tuple`) The list of composition operators
#:
#: - ``'undefined'``
#: - ``'no'``
#: - ``'add'`` - Only available with ImageMagick-6
#: - ``'alpha'`` - Only available with ImageMagick-7
#: - ``'atop'``
#: - ``'blend'``
#: - ``'blur'`` - Only available with ImageMagick-7
#: - ``'bumpmap'``
#: - ``'change_mask'``
#: - ``'clear'``
#: - ``'color_burn'``
#: - ``'color_dodge'``
#: - ``'colorize'``
#: - ``'copy_black'``
#: - ``'copy_blue'``
#: - ``'copy'``
#: - ``'copy_alpha'`` - Only available with ImageMagick-7
#: - ``'copy_cyan'``
#: - ``'copy_green'``
#: - ``'copy_magenta'``
#: - ``'copy_opacity'`` - Only available with ImageMagick-6
#: - ``'copy_red'``
#: - ``'copy_yellow'``
#: - ``'darken'``
#: - ``'darken_intensity'`` - Only available with ImageMagick-7
#: - ``'dst_atop'``
#: - ``'dst'``
#: - ``'dst_in'``
#: - ``'dst_out'``
#: - ``'dst_over'``
#: - ``'difference'``
#: - ``'displace'``
#: - ``'dissolve'``
#: - ``'distort'`` - Only available with ImageMagick-7
#: - ``'divide'`` - Only available with ImageMagick-6
#: - ``'exclusion'``
#: - ``'hard_light'``
#: - ``'head_mix'`` - Only available with ImageMagick-7
#: - ``'hue'``
#: - ``'in'``
#: - ``'intensity'`` - Only available with ImageMagick-7
#: - ``'lighten'``
#: - ``'lighten_intensity'`` - Only available with ImageMagick-7
#: - ``'linear_burn'`` - Only available with ImageMagick-7
#: - ``'linear_dodge'`` - Only available with ImageMagick-7
#: - ``'linear_light'``
#: - ``'luminize'``
#: - ``'mathematics'`` - Only available with ImageMagick-7
#: - ``'minus'`` - Only available with ImageMagick-6
#: - ``'minus_dst'`` - Only available with ImageMagick-7
#: - ``'minus_src'`` - Only available with ImageMagick-7
#: - ``'modulate'``
#: - ``'modulate_add'`` - Only available with ImageMagick-7
#: - ``'modulate_subtract'`` - Only available with ImageMagick-7
#: - ``'multiply'``
#: - ``'out'``
#: - ``'over'``
#: - ``'overlay'``
#: - ``'pegtop_light'`` - Only available with ImageMagick-7
#: - ``'plus'``
#: - ``'replace'``
#: - ``'saturate'``
#: - ``'screen'``
#: - ``'soft_light'``
#: - ``'src_atop'``
#: - ``'src'``
#: - ``'src_in'``
#: - ``'src_out'``
#: - ``'src_over'``
#: - ``'subtract'`` - Only available with ImageMagick-6
#: - ``'threshold'``
#: - ``'vivid_light'`` - Only available with ImageMagick-7
#: - ``'xor'``
#:
#: .. versionchanged:: 0.3.0
#:    Renamed from :const:`COMPOSITE_OPS` to :const:`COMPOSITE_OPERATORS`.
#:
#: .. seealso::
#:
#:    `Compositing Images`__ ImageMagick v6 Examples
#:       Image composition is the technique of combining images that have,
#:       or do not have, transparency or an alpha channel.
#:       This is usually performed using the IM :program:`composite` command.
#:       It may also be performed as either part of a larger sequence of
#:       operations or internally by other image operators.
#:
#:    `ImageMagick Composition Operators`__
#:       Demonstrates the results of applying the various composition
#:       composition operators.
#:
#:    __ http://www.imagemagick.org/Usage/compose/
#:    __ http://www.rubblewebs.co.uk/imagemagick/operators/compose.php
COMPOSITE_OPERATORS = (
    'undefined', 'no', 'add', 'atop', 'blend', 'bumpmap', 'change_mask',
    'clear', 'color_burn', 'color_dodge', 'colorize', 'copy_black',
    'copy_blue', 'copy', 'copy_cyan', 'copy_green', 'copy_magenta',
    'copy_opacity', 'copy_red', 'copy_yellow', 'darken', 'dst_atop', 'dst',
    'dst_in', 'dst_out', 'dst_over', 'difference', 'displace', 'dissolve',
    'exclusion', 'hard_light', 'hue', 'in', 'lighten', 'linear_light',
    'luminize', 'minus', 'modulate', 'multiply', 'out', 'over', 'overlay',
    'plus', 'replace', 'saturate', 'screen', 'soft_light', 'src_atop', 'src',
    'src_in', 'src_out', 'src_over', 'subtract', 'threshold', 'xor', 'divide'
)
if MAGICK_VERSION_NUMBER >= 0x700:  # pragma: no cover
    COMPOSITE_OPERATORS = (
        'undefined', 'alpha', 'atop', 'blend', 'blur', 'bumpmap',
        'change_mask', 'clear', 'color_burn', 'color_dodge', 'colorize',
        'copy_black', 'copy_blue', 'copy', 'copy_cyan', 'copy_green',
        'copy_magenta', 'copy_alpha', 'copy_red', 'copy_yellow', 'darken',
        'darken_intensity', 'difference', 'displace', 'dissolve', 'distort',
        'divide_dst', 'divide_src', 'dst_atop', 'dst', 'dst_in', 'dst_out',
        'dst_over', 'exclusion', 'hard_light', 'hard_mix', 'hue', 'in',
        'intensity', 'lighten', 'lighten_intensity', 'linear_burn',
        'linear_dodge', 'linear_light', 'luminize', 'mathematics', 'minus_dst',
        'minus_src', 'modulate', 'modulus_add', 'modulus_subtract', 'multiply',
        'no', 'out', 'over', 'overlay', 'pegtop_light', 'pin_light', 'plus',
        'replace', 'saturate', 'screen', 'soft_light', 'src_atop', 'src',
        'src_in', 'src_out', 'src_over', 'threshold', 'vivid_light', 'xor'
    )

#: (:class:`tuple`) The list of :attr:`Image.compression` types.
#:
#: .. versionadded:: 0.3.6
#: .. versionchanged:: 0.5.0
#:    Support for ImageMagick-6 & ImageMagick-7
COMPRESSION_TYPES = (
    'undefined', 'no', 'bzip', 'dxt1', 'dxt3', 'dxt5',
    'fax', 'group4', 'jpeg', 'jpeg2000', 'losslessjpeg',
    'lzw', 'rle', 'zip', 'zips', 'piz', 'pxr24', 'b44',
    'b44a', 'lzma', 'jbig1', 'jbig2'
)
if MAGICK_VERSION_NUMBER >= 0x700:  # pragma: no cover
    COMPRESSION_TYPES = (
        'undefined', 'b44a', 'b44', 'bzip', 'dxt1', 'dxt3', 'dxt5', 'fax',
        'group4', 'jbig1', 'jbig2', 'jpeg2000', 'jpeg', 'losslessjpeg',
        'lzma', 'lzw', 'no', 'piz', 'pxr24', 'rle', 'zip', 'zips'
    )

#: (:class:`tuple`) The list of :attr:`BaseImage.dispose` types.
#:
#: .. versionadded:: 0.5.0
DISPOSE_TYPES = (
    'undefined',
    'none',
    'background',
    'previous'
)


#: (:class:`tuple`) The list of :meth:`BaseImage.distort` methods.
#:
#: - ``'undefined'``
#: - ``'affine'``
#: - ``'affine_projection'``
#: - ``'scale_rotate_translate'``
#: - ``'perspective'``
#: - ``'perspective_projection'``
#: - ``'bilinear_forward'``
#: - ``'bilinear_reverse'``
#: - ``'polynomial'``
#: - ``'arc'``
#: - ``'polar'``
#: - ``'depolar'``
#: - ``'cylinder_2_plane'``
#: - ``'plane_2_cylinder'``
#: - ``'barrel'``
#: - ``'barrel_inverse'``
#: - ``'shepards'``
#: - ``'resize'``
#: - ``'sentinel'``
#:
#: .. versionadded:: 0.4.1
DISTORTION_METHODS = (
    'undefined', 'affine', 'affine_projection', 'scale_rotate_translate',
    'perspective', 'perspective_projection', 'bilinear_forward',
    'bilinear_reverse', 'polynomial', 'arc', 'polar', 'depolar',
    'cylinder_2_plane', 'plane_2_cylinder', 'barrel', 'barrel_inverse',
    'shepards', 'resize', 'sentinel'
)


#: (:class:`tuple`) The list of Dither methods. Used by
#: :meth:`Image.posterize() <BaseImage.posterize>` and
#: :meth:`Image.remap() <BaseImage.remap>` methods.
#:
#: - ``'undefined'``
#: - ``'no'``
#: - ``'riemersma'``
#: - ``'floyd_steinberg'``
#:
#: .. versionadded:: 0.5.0
DITHER_METHODS = ('undefined', 'no', 'riemersma', 'floyd_steinberg')


#: (:class:`tuple`) The list of evaluation operators. Used by
#: :meth:`Image.evaluate() <BaseImage.evaluate>` method.
#:
#: - ``'undefined'``
#: - ``'abs'``
#: - ``'add'``
#: - ``'addmodulus'``
#: - ``'and'``
#: - ``'cosine'``
#: - ``'divide'``
#: - ``'exponential'``
#: - ``'gaussiannoise'``
#: - ``'impulsenoise'``
#: - ``'laplaciannoise'``
#: - ``'leftshift'``
#: - ``'log'``
#: - ``'max'``
#: - ``'mean'``
#: - ``'median'``
#: - ``'min'``
#: - ``'multiplicativenoise'``
#: - ``'multiply'``
#: - ``'or'``
#: - ``'poissonnoise'``
#: - ``'pow'``
#: - ``'rightshift'``
#: - ``'set'``
#: - ``'sine'``
#: - ``'subtract'``
#: - ``'sum'``
#: - ``'threshold'``
#: - ``'thresholdblack'``
#: - ``'thresholdwhite'``
#: - ``'uniformnoise'``
#: - ``'xor'``
#:
#: .. seealso::
#:
#:    `ImageMagick Image Evaluation Operators`__
#:       Describes the MagickEvaluateImageChannel method and lists the
#:       various evaluations operators
#:
#:    __ http://www.magickwand.org/MagickEvaluateImage.html
EVALUATE_OPS = ('undefined', 'add', 'and', 'divide', 'leftshift', 'max',
                'min', 'multiply', 'or', 'rightshift', 'set', 'subtract',
                'xor', 'pow', 'log', 'threshold', 'thresholdblack',
                'thresholdwhite', 'gaussiannoise', 'impulsenoise',
                'laplaciannoise', 'multiplicativenoise', 'poissonnoise',
                'uniformnoise', 'cosine', 'sine', 'addmodulus', 'mean',
                'abs', 'exponential', 'median', 'sum', 'rootmeansquare')
if MAGICK_VERSION_NUMBER >= 0x700:  # pragma: no cover
    EVALUATE_OPS = ('undefined', 'abs', 'add', 'addmodulus', 'and', 'cosine',
                    'divide', 'exponential', 'gaussiannoise', 'impulsenoise',
                    'laplaciannoise', 'leftshift', 'log', 'max', 'mean',
                    'median', 'min', 'multiplicativenoise', 'multiply', 'or',
                    'poissonnoise', 'pow', 'rightshift', 'rootmeansquare',
                    'set', 'sine', 'subtract', 'sum', 'thresholdblack',
                    'threshold', 'thresholdwhite', 'uniformnoise', 'xor')


#: (:class:`tuple`) The list of filter types. Used by
#: :meth:`Image.resample() <BaseImage.resample>` and
#: :meth:`Image.resize() <BaseImage.resize>` methods.
#:
#: - ``'undefined'``
#: - ``'point'``
#: - ``'box'``
#: - ``'triangle'``
#: - ``'hermite'``
#: - ``'hanning'``
#: - ``'hamming'``
#: - ``'blackman'``
#: - ``'gaussian'``
#: - ``'quadratic'``
#: - ``'cubic'``
#: - ``'catrom'``
#: - ``'mitchell'``
#: - ``'jinc'``
#: - ``'sinc'``
#: - ``'sincfast'``
#: - ``'kaiser'``
#: - ``'welsh'``
#: - ``'parzen'``
#: - ``'bohman'``
#: - ``'bartlett'``
#: - ``'lagrange'``
#: - ``'lanczos'``
#: - ``'lanczossharp'``
#: - ``'lanczos2'``
#: - ``'lanczos2sharp'``
#: - ``'robidoux'``
#: - ``'robidouxsharp'``
#: - ``'cosine'``
#: - ``'spline'``
#: - ``'sentinel'``
#:
#: .. seealso::
#:
#:    `ImageMagick Resize Filters`__
#:       Demonstrates the results of resampling images using the various
#:       resize filters and blur settings available in ImageMagick.
#:
#:    __ http://www.imagemagick.org/Usage/resize/
FILTER_TYPES = ('undefined', 'point', 'box', 'triangle', 'hermite', 'hanning',
                'hamming', 'blackman', 'gaussian', 'quadratic', 'cubic',
                'catrom', 'mitchell', 'jinc', 'sinc', 'sincfast', 'kaiser',
                'welsh', 'parzen', 'bohman', 'bartlett', 'lagrange', 'lanczos',
                'lanczossharp', 'lanczos2', 'lanczos2sharp', 'robidoux',
                'robidouxsharp', 'cosine', 'spline', 'sentinel')


#: (:class:`tuple`) The list of :attr:`Image.function <BaseImage.function>`
#: types.
#:
#: - ``'undefined'``
#: - ``'arcsin'``
#: - ``'arctan'``
#: - ``'polynomial'``
#: - ``'sinusoid'``
FUNCTION_TYPES = ('undefined', 'polynomial', 'sinusoid', 'arcsin', 'arctan')
if MAGICK_VERSION_NUMBER >= 0x700:  # pragma: no cover
    FUNCTION_TYPES = ('undefined', 'arcsin', 'arctan', 'polynomial',
                      'sinusoid')


#: (:class:`tuple`) The list of :attr:`~BaseImage.gravity` types.
#:
#: - ``'forget'``
#: - ``'north_west'``
#: - ``'north'``
#: - ``'north_east'``
#: - ``'west'``
#: - ``'center'``
#: - ``'east'``
#: - ``'south_west'``
#: - ``'south'``
#: - ``'south_east'``
#:
#: .. versionadded:: 0.3.0
GRAVITY_TYPES = ('forget', 'north_west', 'north', 'north_east', 'west',
                 'center', 'east', 'south_west', 'south', 'south_east',
                 'static')


#: (:class:`tuple`) The list of methods for :meth:`~BaseImage.merge_layers`
#: and :meth:`~Image.compare_layers`.
#:
#: - ``'undefined'``
#: - ``'coalesce'``
#: - ``'compareany'`` - Only used for :meth:`~Image.compare_layers`.
#: - ``'compareclear'`` - Only used for :meth:`~Image.compare_layers`.
#: - ``'compareoverlay'`` - Only used for :meth:`~Image.compare_layers`.
#: - ``'dispose'``
#: - ``'optimize'``
#: - ``'optimizeimage'``
#: - ``'optimizeplus'``
#: - ``'optimizetrans'``
#: - ``'removedups'``
#: - ``'removezero'``
#: - ``'composite'``
#: - ``'merge'`` - Only used for :meth:`~BaseImage.merge_layers`.
#: - ``'flatten'`` - Only used for :meth:`~BaseImage.merge_layers`.
#: - ``'mosaic'`` - Only used for :meth:`~BaseImage.merge_layers`.
#: - ``'trimbounds'`` - Only used for :meth:`~BaseImage.merge_layers`.
#:
#: .. versionadded:: 0.4.3
IMAGE_LAYER_METHOD = ('undefined', 'coalesce', 'compareany', 'compareclear',
                      'compareoverlay', 'dispose', 'optimize', 'optimizeimage',
                      'optimizeplus', 'optimizetrans', 'removedups',
                      'removezero', 'composite', 'merge', 'flatten', 'mosaic',
                      'trimbounds')


#: (:class:`tuple`) The list of image types
#:
#: - ``'undefined'``
#: - ``'bilevel'``
#: - ``'grayscale'``
#: - ``'grayscalealpha'`` - Only available with ImageMagick-7
#: - ``'grayscalematte'`` - Only available with ImageMagick-6
#: - ``'palette'``
#: - ``'palettealpha'`` - Only available with ImageMagick-7
#: - ``'palettematte'`` - Only available with ImageMagick-6
#: - ``'truecolor'``
#: - ``'truecoloralpha'`` - Only available with ImageMagick-7
#: - ``'truecolormatte'`` - Only available with ImageMagick-6
#: - ``'colorseparation'``
#: - ``'colorseparationalpha'`` - Only available with ImageMagick-7
#: - ``'colorseparationmatte'`` - Only available with ImageMagick-6
#: - ``'optimize'``
#: - ``'palettebilevelalpha'`` - Only available with ImageMagick-7
#: - ``'palettebilevelmatte'`` - Only available with ImageMagick-6
#:
#: .. seealso::
#:
#:    `ImageMagick Image Types`__
#:       Describes the MagickSetImageType method which can be used
#:       to set the type of an image
#:
#:    __ http://www.imagemagick.org/api/magick-image.php#MagickSetImageType
IMAGE_TYPES = ('undefined', 'bilevel', 'grayscale', 'grayscalematte',
               'palette', 'palettematte', 'truecolor', 'truecolormatte',
               'colorseparation', 'colorseparationmatte', 'optimize',
               'palettebilevelmatte')
if MAGICK_VERSION_NUMBER >= 0x700:  # pragma: no cover
    IMAGE_TYPES = ('undefined', 'bilevel', 'grayscale', 'grayscalemalpha',
                   'palette', 'palettealpha', 'truecolor', 'truecoloralpha',
                   'colorseparation', 'colorseparationalpha', 'optimize',
                   'palettebilevelalpha')


#: (:class:`tuple`) The list of interlace schemes.
#:
#: - ``'undefined'``
#: - ``'no'``
#: - ``'line'``
#: - ``'plane'``
#: - ``'partition'``
#: - ``'gif'``
#: - ``'jpeg'``
#: - ``'png'``
#:
#: .. versionadded:: 0.5.2
INTERLACE_TYPES = ('undefined', 'no', 'line', 'plane', 'partition', 'gif',
                   'jpeg', 'png')


#: (:class:`tuple`) The list of builtin kernels.
#:
#: - ``'undefined'``
#: - ``'unity'``
#: - ``'gaussian'``
#: - ``'dog'``
#: - ``'log'``
#: - ``'blur'``
#: - ``'comet'``
#: - ``'laplacian'``
#: - ``'sobel'``
#: - ``'frei_chen'``
#: - ``'roberts'``
#: - ``'prewitt'``
#: - ``'compass'``
#: - ``'kirsch'``
#: - ``'diamond'``
#: - ``'square'``
#: - ``'rectangle'``
#: - ``'octagon'``
#: - ``'disk'``
#: - ``'plus'``
#: - ``'cross'``
#: - ``'ring'``
#: - ``'peaks'``
#: - ``'edges'``
#: - ``'corners'``
#: - ``'diagonals'``
#: - ``'line_ends'``
#: - ``'line_junctions'``
#: - ``'ridges'``
#: - ``'convex_hull'``
#: - ``'thin_se'``
#: - ``'skeleton'``
#: - ``'chebyshev'``
#: - ``'manhattan'``
#: - ``'octagonal'``
#: - ``'euclidean'``
#: - ``'user_defined'``
#: - ``'binomial'``
#:
KERNEL_INFO_TYPES = ('undefined', 'unity', 'gaussian', 'dog', 'log', 'blur',
                     'comet', 'laplacian', 'sobel', 'frei_chen', 'roberts',
                     'prewitt', 'compass', 'kirsch', 'diamond', 'square',
                     'rectangle', 'octagon', 'disk', 'plus', 'cross', 'ring',
                     'peaks', 'edges', 'corners', 'diagonals', 'line_ends',
                     'line_junctions', 'ridges', 'convex_hull', 'thin_se',
                     'skeleton', 'chebyshev', 'manhattan', 'octagonal',
                     'euclidean', 'user_defined', 'binomial')
if MAGICK_VERSION_NUMBER >= 0x700:  # pragma: no cover
    KERNEL_INFO_TYPES = ('undefined', 'unity', 'gaussian', 'dog', 'log',
                         'blur', 'comet', 'binomial', 'laplacian', 'sobel',
                         'frei_chen', 'roberts', 'prewitt', 'compass',
                         'kirsch', 'diamond', 'square', 'rectangle', 'octagon',
                         'disk', 'plus', 'cross', 'ring', 'peaks', 'edges',
                         'corners', 'diagonals', 'line_ends', 'line_junctions',
                         'ridges', 'convex_hull', 'thin_se', 'skeleton',
                         'chebyshev', 'manhattan', 'octagonal', 'euclidean',
                         'user_defined')

#: (:class:`tuple`) The list of morphology methods.
#:
#: - ``'undefined'``
#: - ``'convolve'``
#: - ``'correlate'``
#: - ``'erode'``
#: - ``'dilate'``
#: - ``'erode_intensity'``
#: - ``'dilate_intensity'``
#: - ``'distance'``
#: - ``'open'``
#: - ``'close'``
#: - ``'open_intensity'``
#: - ``'close_intensity'``
#: - ``'smooth'``
#: - ``'edgein'``
#: - ``'edgeout'``
#: - ``'edge'``
#: - ``'tophat'``
#: - ``'bottom_hat'``
#: - ``'hit_and_miss'``
#: - ``'thinning'``
#: - ``'thicken'``
#: - ``'voronoi'``
#: - ``'iterative_distance'``
#:
MORPHOLOGY_METHODS = ('undefined', 'convolve', 'correlate', 'erode', 'dilate',
                      'erode_intensity', 'dilate_intensity', 'distance',
                      'open', 'close', 'open_intensity', 'close_intensity',
                      'smooth', 'edgein', 'edgeout', 'edge', 'tophat',
                      'bottom_hat', 'hit_and_miss', 'thinning', 'thicken',
                      'voronoi', 'iterative_distance')
if MAGICK_VERSION_NUMBER >= 0x700:  # pragma: no cover
    MORPHOLOGY_METHODS = ('undefined', 'convolve', 'correlate', 'erode',
                          'dilate', 'erode_intensity', 'dilate_intensity',
                          'iterative_distance', 'open', 'close',
                          'open_intensity', 'close_intensity', 'smooth',
                          'edgein', 'edgeout', 'edge', 'tophat', 'bottom_hat',
                          'hit_and_miss', 'thinning', 'thicken', 'distance',
                          'voronoi')


#: (:class:`tuple`) The list of noise types used by
#: :meth:`Image.noise() <wand.image.BaseImage.noise>` method.
#:
#: - ``'undefined'``
#: - ``'uniform'``
#: - ``'gaussian'``
#: - ``'multiplicative_gaussian'``
#: - ``'impulse'``
#: - ``'laplacian'``
#: - ``'poisson'``
#: - ``'random'``
#:
#: .. versionadded:: 0.5.3
NOISE_TYPES = ('undefined', 'uniform', 'gaussian', 'multiplicative_gaussian',
               'impulse', 'laplacian', 'poisson', 'random')


#: (:class:`collections.abc.Set`) The set of available
#: :attr:`~BaseImage.options`.
#:
#: .. versionadded:: 0.3.0
#:
#: .. versionchanged:: 0.3.4
#:    Added ``'jpeg:sampling-factor'`` option.
#:
#: .. versionchanged:: 0.3.9
#:    Added ``'pdf:use-cropbox'`` option. Ensure you set this option *before*
#:    reading the PDF document.
#:
#: .. deprecated:: 0.5.0
#:    Any arbitrary key can be set to the option table. Key-Value pairs set
#:    on the MagickWand stack allowing for various coders, kernels, morphology
#:    (&tc) to pick and choose additional user-supplied properties/artifacts.
OPTIONS = frozenset([
    'caption',
    'comment',
    'date:create',
    'date:modify',
    'exif:ColorSpace',
    'exif:InteroperabilityIndex',
    'fill',
    'film-gamma',
    'gamma',
    'hdr:exposure',
    'jpeg:colorspace',
    'jpeg:sampling-factor',
    'label',
    'pdf:use-cropbox',
    'png:bit-depth-written',
    'png:IHDR.bit-depth-orig',
    'png:IHDR.color-type-orig',
    'png:tIME',
    'reference-black',
    'reference-white',
    'signature',
    'tiff:Orientation',
    'tiff:photometric',
    'tiff:ResolutionUnit',
    'type:hinting',
    'vips:metadata'
])


#: (:class:`tuple`) The list of :attr:`~BaseImage.orientation` types.
#:
#: .. versionadded:: 0.3.0
ORIENTATION_TYPES = ('undefined', 'top_left', 'top_right', 'bottom_right',
                     'bottom_left', 'left_top', 'right_top', 'right_bottom',
                     'left_bottom')


#: (:class:`tuple`) List of interpolate pixel methods (ImageMagick-7 only.)
#:
#: - ``'undefined'``
#: - ``'average'``
#: - ``'average9'``
#: - ``'average16'``
#: - ``'background'``
#: - ``'bilinear'``
#: - ``'blend'``
#: - ``'catrom'``
#: - ``'integer'``
#: - ``'mesh'``
#: - ``'nearest'``
#: - ``'spline'``
#:
#: .. versionadded:: 0.5.0
PIXEL_INTERPOLATE_METHODS = ('undefined', 'average', 'average9', 'average16',
                             'background', 'bilinear', 'blend', 'catrom',
                             'integer', 'mesh', 'nearest', 'spline')


#: (:class:`tuple`) List of rendering intent types used for
#: :attr:`Image.rendering_intent <wand.image.BaseImage.rendering_intent>`
#: property.
#:
#: - ``'undefined'``
#: - ``'saturation'``
#: - ``'perceptual'``
#: - ``'absolute'``
#: - ``'relative'``
#:
#: .. versionadded:: 0.5.4
RENDERING_INTENT_TYPES = ('undefined', 'saturation', 'perceptual', 'absolute',
                          'relative')


#: (:class:`tuple`) List of sparse color methods used by
#: :class:`Image.sparse_color() <wand.image.BaseImage.sparse_color>`
#:
#: - ``'undefined'``
#: - ``'barycentric'``
#: - ``'bilinear'``
#: - ``'shepards'``
#: - ``'voronoi'``
#: - ``'inverse'``
#: - ``'manhattan'``
#:
#: .. versionadded:: 0.5.3
SPARSE_COLOR_METHODS = dict(undefined=0, barycentric=1, bilinear=7,
                            shepards=16, voronoi=18, inverse=19,
                            manhattan=20)


#: (:class:`tuple`) The list of statistic types used by
#: :meth:`Image.statistic() <wand.image.BaseImage.statistic>`.
#:
#: - ``'undefined'``
#: - ``'gradient'``
#: - ``'maximum'``
#: - ``'mean'``
#: - ``'median'``
#: - ``'minimum'``
#: - ``'mode'``
#: - ``'nonpeak'``
#: - ``'root_mean_square'``
#: - ``'standard_deviation'``
#:
#: .. versionadded:: 0.5.3
STATISTIC_TYPES = ('undefined', 'gradient', 'maximum', 'mean', 'median',
                   'minimum', 'mode', 'nonpeak', 'standard_deviation',
                   'root_mean_square')
if MAGICK_VERSION_NUMBER >= 0x700:  # pragma: no cover
    STATISTIC_TYPES = ('undefined', 'gradient', 'maximum', 'mean', 'median',
                       'minimum', 'mode', 'nonpeak', 'root_mean_square',
                       'standard_deviation')


#: (:class:`tuple`) The list of pixel storage types.
#:
#: - ``'undefined'``
#: - ``'char'``
#: - ``'double'``
#: - ``'float'``
#: - ``'integer'``
#: - ``'long'``
#: - ``'quantum'``
#: - ``'short'``
#:
#: .. versionadded:: 0.5.0
STORAGE_TYPES = ('undefined', 'char', 'double', 'float', 'integer',
                 'long', 'quantum', 'short')


#: (:class:`tuple`) The list of resolution unit types.
#:
#: - ``'undefined'``
#: - ``'pixelsperinch'``
#: - ``'pixelspercentimeter'``
#:
#: .. seealso::
#:
#:    `ImageMagick Image Units`__
#:       Describes the MagickSetImageUnits method which can be used
#:       to set image units of resolution
#:
#:    __ http://www.imagemagick.org/api/magick-image.php#MagickSetImageUnits
UNIT_TYPES = ('undefined', 'pixelsperinch', 'pixelspercentimeter')


#: (:class:`tuple`) The list of :attr:`~BaseImage.virtual_pixel` types.
#:
#: - ``'undefined'``
#: - ``'background'``
#: - ``'constant'`` - Only available with ImageMagick-6
#: - ``'dither'``
#: - ``'edge'``
#: - ``'mirror'``
#: - ``'random'``
#: - ``'tile'``
#: - ``'transparent'``
#: - ``'mask'``
#: - ``'black'``
#: - ``'gray'``
#: - ``'white'``
#: - ``'horizontal_tile'``
#: - ``'vertical_tile'``
#: - ``'horizontal_tile_edge'``
#: - ``'vertical_tile_edge'``
#: - ``'checker_tile'``
#:
#: .. versionadded:: 0.4.1
VIRTUAL_PIXEL_METHOD = ('undefined', 'background', 'constant', 'dither',
                        'edge', 'mirror', 'random', 'tile', 'transparent',
                        'mask', 'black', 'gray', 'white', 'horizontal_tile',
                        'vertical_tile', 'horizontal_tile_edge',
                        'vertical_tile_edge', 'checker_tile')
if MAGICK_VERSION_NUMBER >= 0x700:  # pragma: no cover
    VIRTUAL_PIXEL_METHOD = ('undefined', 'background', 'dither',
                            'edge', 'mirror', 'random', 'tile', 'transparent',
                            'mask', 'black', 'gray', 'white',
                            'horizontal_tile', 'vertical_tile',
                            'horizontal_tile_edge', 'vertical_tile_edge',
                            'checker_tile')


def manipulative(function):
    """Mark the operation manipulating itself instead of returning new one."""
    @functools.wraps(function)
    def wrapped(self, *args, **kwargs):
        result = function(self, *args, **kwargs)
        self.dirty = True
        return result
    return wrapped


def trap_exception(function):
    @functools.wraps(function)
    def wrapped(self, *args, **kwargs):
        result = function(self, *args, **kwargs)
        if not bool(result):
            self.raise_exception()
        return result
    return wrapped


class BaseImage(Resource):
    """The abstract base of :class:`Image` (container) and
    :class:`~wand.sequence.SingleImage`.  That means the most of
    operations, defined in this abstract class, are possible for
    both :class:`Image` and :class:`~wand.sequence.SingleImage`.

    .. versionadded:: 0.3.0

    """

    #: (:class:`OptionDict`) The mapping of internal option settings.
    #:
    #: .. versionadded:: 0.3.0
    #:
    #: .. versionchanged:: 0.3.4
    #:    Added ``'jpeg:sampling-factor'`` option.
    #:
    #: .. versionchanged:: 0.3.9
    #:    Added ``'pdf:use-cropbox'`` option.
    options = None

    #: (:class:`collections.abc.Sequence`) The list of
    #: :class:`~wand.sequence.SingleImage`\ s that the image contains.
    #:
    #: .. versionadded:: 0.3.0
    sequence = None

    #: (:class:`bool`) Whether the image is changed or not.
    dirty = None

    #: (:class:`numbers.Integral`) Internal placeholde for
    #: :attr:`seed` property.
    #:
    #: .. versionadded:: 0.5.5
    _seed = None

    c_is_resource = library.IsMagickWand
    c_destroy_resource = library.DestroyMagickWand
    c_get_exception = library.MagickGetException
    c_clear_exception = library.MagickClearException

    __slots__ = '_wand',

    def __init__(self, wand):
        self.wand = wand
        self.channel_images = ChannelImageDict(self)
        self.channel_depths = ChannelDepthDict(self)
        self.options = OptionDict(self)
        self.dirty = False

    def __eq__(self, other):
        if isinstance(other, type(self)):
            return self.signature == other.signature
        return False

    def __getitem__(self, idx):
        if (not isinstance(idx, string_type) and
                isinstance(idx, abc.Iterable)):
            idx = tuple(idx)
            d = len(idx)
            if not (1 <= d <= 2):
                raise ValueError('index cannot be {0}-dimensional'.format(d))
            elif d == 2:
                x, y = idx
                x_slice = isinstance(x, slice)
                y_slice = isinstance(y, slice)
                if x_slice and not y_slice:
                    y = slice(y, y + 1)
                elif not x_slice and y_slice:
                    x = slice(x, x + 1)
                elif not (x_slice or y_slice):
                    if not (isinstance(x, numbers.Integral) and
                            isinstance(y, numbers.Integral)):
                        raise TypeError('x and y must be integral, not ' +
                                        repr((x, y)))
                    if x < 0:
                        x += self.width
                    if y < 0:
                        y += self.height
                    if x >= self.width:
                        raise IndexError('x must be less than width')
                    elif y >= self.height:
                        raise IndexError('y must be less than height')
                    elif x < 0:
                        raise IndexError('x cannot be less than 0')
                    elif y < 0:
                        raise IndexError('y cannot be less than 0')
                    with iter(self) as iterator:
                        iterator.seek(y)
                        return iterator.next(x)
                if not (x.step is None and y.step is None):
                    raise ValueError('slicing with step is unsupported')
                elif (x.start is None and x.stop is None and
                      y.start is None and y.stop is None):
                    return self.clone()
                cloned = self.clone()
                try:
                    cloned.crop(x.start, y.start, x.stop, y.stop)
                except ValueError as e:
                    raise IndexError(str(e))
                return cloned
            else:
                return self[idx[0]]
        elif isinstance(idx, numbers.Integral):
            if idx < 0:
                idx += self.height
            elif idx >= self.height:
                raise IndexError('index must be less than height, but got ' +
                                 repr(idx))
            elif idx < 0:
                raise IndexError('index cannot be less than zero, but got ' +
                                 repr(idx))
            with iter(self) as iterator:
                iterator.seek(idx)
                return iterator.next()
        elif isinstance(idx, slice):
            return self[:, idx]
        raise TypeError('unsupported index type: ' + repr(idx))

    def __setitem__(self, idx, color):
        if isinstance(color, string_type):
            color = Color(color)
        assertions.assert_color(color=color)
        if not isinstance(idx, abc.Iterable):
            raise TypeError('Expecting list of x,y coordinates, not ' +
                            repr(idx))
        idx = tuple(idx)
        if len(idx) != 2:
            msg = 'pixel index can not be {0}-dimensional'.format(len(idx))
            raise ValueError(msg)
        colorspace = self.colorspace
        s_index = STORAGE_TYPES.index("double")
        width, height = self.size
        x1, y1 = idx
        x2, y2 = 1, 1
        if not (isinstance(x1, numbers.Integral) and
                isinstance(y1, numbers.Integral)):
            raise TypeError('Expecting x & y to be integers')
        if x1 < 0:
            x1 += width
        if y1 < 0:
            y1 += height
        if x1 >= width:
            raise ValueError('x must be less then image width')
        elif y1 >= height:
            raise ValueError('y must be less then image height')
        if colorspace == 'gray':
            channel_map = b'I'
            pixel = (ctypes.c_double * 1)()
            pixel[0] = color.red
        elif colorspace == 'cmyk':
            channel_map = b'CMYK'
            pixel = (ctypes.c_double * 5)()
            pixel[0] = color.red
            pixel[1] = color.green
            pixel[2] = color.blue
            pixel[3] = color.black
            if self.alpha_channel:
                channel_map += b'A'
                pixel[4] = color.alpha
        else:
            channel_map = b'RGB'
            pixel = (ctypes.c_double * 4)()
            pixel[0] = color.red
            pixel[1] = color.green
            pixel[2] = color.blue
            if self.alpha_channel:
                channel_map += b'A'
                pixel[3] = color.alpha
        r = library.MagickImportImagePixels(self.wand,
                                            x1, y1, x2, y2,
                                            channel_map,
                                            s_index,
                                            ctypes.byref(pixel))
        if not r:
            self.raise_exception()

    def __hash__(self):
        return hash(self.signature)

    def __iter__(self):
        return Iterator(image=self)

    def __len__(self):
        return self.height

    def __ne__(self, other):
        return not (self == other)

    def __repr__(self, extra_format=' ({self.width}x{self.height})'):
        cls = type(self)
        typename = '{0}.{1}'.format(
            cls.__module__,
            getattr(cls, '__qualname__', cls.__name__)
        )
        if getattr(self, 'c_resource', None) is None:
            return '<{0}: (closed)>'.format(typename)
        sig = self.signature
        if not sig:
            return '<{0}: (empty)>'.format(typename)
        return '<{0}: {1}{2}>'.format(
            typename, sig[:7], extra_format.format(self=self)
        )

    @property
    def __array_interface__(self):
        """Allows image-data from :class:`Image <wand.image.BaseImage>`
        instances to be loaded into numpy's array.

        .. code::

            import numpy
            from wand.image import Image

            with Image(filename='rose:') as img:
                img_data = numpy.asarray(img)

        :raises ValueError: if image has no data.

        .. versionadded:: 0.5.0
        """
        if not self.signature:
            raise ValueError("No image data to interface with.")
        width, height = self.size
        storage_type = 1  # CharPixel
        channel_format = binary("RGB")
        channel_number = 3
        if self.alpha_channel:
            channel_format = binary("RGBA")
            channel_number = 4
        c_buffer = (width * height * channel_number * ctypes.c_char)()
        # FIXME: Move to pixel-data import/export methods.
        r = library.MagickExportImagePixels(self.wand,
                                            0, 0, width, height,
                                            channel_format, storage_type,
                                            ctypes.byref(c_buffer))
        if not r:
            self.raise_exception()
        return dict(data=(ctypes.addressof(c_buffer), True),
                    shape=(width, height, channel_number),
                    typestr='|u1',
                    version=3,
                    _c_buffer=c_buffer)  # Need to hold reference count.

    @property
    def alpha_channel(self):
        """(:class:`bool`) Get state of image alpha channel.
        It can also be used to enable/disable alpha channel, but with different
        behavior new, copied, or existing.

        Behavior of setting :attr:`alpha_channel` is defined with the
        following values:

        - ``'activate'``, ``'on'``, or :const:`True` will enable an images
           alpha channel. Existing alpha data is preserved.
        - ``'deactivate'``, ``'off'``, or :const:`False` will disable an images
           alpha channel. Any data on the alpha will be preserved.
        - ``'associate'`` & ``'disassociate'`` toggle alpha channel flag in
           certain image-file specifications.
        - ``'set'`` enables and resets any data in an images alpha channel.
        - ``'opaque'`` enables alpha/matte channel, and forces full opaque
           image.
        - ``'transparent'`` enables alpha/matte channel, and forces full
           transparent image.
        - ``'extract'`` copies data in alpha channel across all other channels,
           and disables alpha channel.
        - ``'copy'`` calculates the gray-scale of RGB channels,
            and applies it to alpha channel.
        - ``'shape'`` is identical to ``'copy'``, but will color the resulting
           image with the value defined with :attr:`background_color`.
        - ``'remove'`` will composite :attr:`background_color` value.
        - ``'background'`` replaces full-transparent color with background
           color.


        .. versionadded:: 0.2.1

        .. versionchanged:: 0.4.1
           Support for additional setting values.
           However :attr:`Image.alpha_channel` will continue to return
           :class:`bool` if the current alpha/matte state is enabled.
        """
        return bool(library.MagickGetImageAlphaChannel(self.wand))

    @alpha_channel.setter
    @manipulative
    def alpha_channel(self, alpha_type):
        is_im6 = MAGICK_VERSION_NUMBER < 0x700
        # Map common aliases for ``'deactivate'``
        if alpha_type is False or (alpha_type == 'off' and is_im6):
            alpha_type = 'deactivate'
        # Map common aliases for ``'activate'``
        elif alpha_type is True or (alpha_type == 'on' and is_im6):
            alpha_type = 'activate'
        assertions.string_in_list(ALPHA_CHANNEL_TYPES,
                                  'wand.image.ALPHA_CHANNEL_TYPES',
                                  alpha_channel=alpha_type)
        alpha_index = ALPHA_CHANNEL_TYPES.index(alpha_type)
        library.MagickSetImageAlphaChannel(self.wand, alpha_index)

    @property
    def animation(self):
        """(:class:`bool`) Whether the image is animation or not.
        It doesn't only mean that the image has two or more images (frames),
        but all frames are even the same size.  It's about image format,
        not content.  It's :const:`False` even if :mimetype:`image/ico`
        consits of two or more images of the same size.

        For example, it's :const:`False` for :mimetype:`image/jpeg`,
        :mimetype:`image/gif`, :mimetype:`image/ico`.

        If :mimetype:`image/gif` has two or more frames, it's :const:`True`.
        If :mimetype:`image/gif` has only one frame, it's :const:`False`.

        .. versionadded:: 0.3.0

        .. versionchanged:: 0.3.8
           Became to accept :mimetype:`image/x-gif` as well.

        """
        return False

    @property
    def antialias(self):
        """(:class:`bool`) If vectors & fonts will use anti-aliasing.

        .. versionchanged:: 0.5.0
           Previosuly named :attr:`font_antialias`.
        """
        return bool(library.MagickGetAntialias(self.wand))

    @antialias.setter
    @manipulative
    def antialias(self, antialias):
        assertions.assert_bool(antialias=antialias)
        library.MagickSetAntialias(self.wand, antialias)

    @property
    def background_color(self):
        """(:class:`wand.color.Color`) The image background color.
        It can also be set to change the background color.

        .. versionadded:: 0.1.9

        """
        pixel = library.NewPixelWand()
        result = library.MagickGetImageBackgroundColor(self.wand, pixel)
        if not result:  # pragma: no cover
            self.raise_exception()
        else:
            color = Color.from_pixelwand(pixel)
            pixel = library.DestroyPixelWand(pixel)
            return color

    @background_color.setter
    @manipulative
    def background_color(self, color):
        if isinstance(color, string_type):
            color = Color(color)
        assertions.assert_color(color=color)
        with color:
            result = library.MagickSetImageBackgroundColor(self.wand,
                                                           color.resource)
            if not result:  # pragma: no cover
                self.raise_exception()

    @property
    def blue_primary(self):
        """(:class:`tuple`) The chromatic blue primary point for the image.
        With ImageMagick-6 the primary value is ``(x, y)`` coordinates;
        however, ImageMagick-7 has ``(x, y, z)``.

        .. versionadded:: 0.5.2
        """
        x = ctypes.c_double(0.0)
        y = ctypes.c_double(0.0)
        r = None
        p = None
        if MAGICK_VERSION_NUMBER < 0x700:
            r = library.MagickGetImageBluePrimary(self.wand, x, y)
            p = (x.value, y.value)
        else:  # pragma: no cover
            z = ctypes.c_double(0.0)
            r = library.MagickGetImageBluePrimary(self.wand, x, y, z)
            p = (x.value, y.value, z.value)
        if not r:  # pragma: no cover
            self.raise_exception()
        return p

    @blue_primary.setter
    def blue_primary(self, coordinates):
        r = None
        if not isinstance(coordinates, abc.Sequence):
            raise TypeError('Primary must be a tuple')
        if MAGICK_VERSION_NUMBER < 0x700:
            x, y = coordinates
            r = library.MagickSetImageBluePrimary(self.wand, x, y)
        else:  # pragma: no cover
            x, y, z = coordinates
            r = library.MagickSetImageBluePrimary(self.wand, x, y, z)
        if not r:  # pragma: no cover
            self.raise_exception()

    @property
    def border_color(self):
        """(:class:`wand.color.Color`) The image border color. Used for
        special effects like :meth:`polaroid()`.

        .. versionadded:: 0.5.4
        """
        pixel = library.NewPixelWand()
        result = library.MagickGetImageBorderColor(self.wand, pixel)
        if not result:  # pragma: no cover
            self.raise_exception()
        else:
            color = Color.from_pixelwand(pixel)
            pixel = library.DestroyPixelWand(pixel)
            return color

    @border_color.setter
    def border_color(self, color):
        if isinstance(color, string_type):
            color = Color(color)
        assertions.assert_color(border_color=color)
        with color:
            r = library.MagickSetImageBorderColor(self.wand, color.resource)
            if not r:  # pragma: no cover
                self.raise_exception()

    @property
    def colors(self):
        """(:class:`numbers.Integral`) Count of unique colors used within the
        image. This is READ ONLY property.

        .. versionadded:: 0.5.3
        """
        return library.MagickGetImageColors(self.wand)

    @property
    def colorspace(self):
        """(:class:`basestring`) The image colorspace.

        Defines image colorspace as in :const:`COLORSPACE_TYPES` enumeration.

        It may raise :exc:`ValueError` when the colorspace is unknown.

        .. versionadded:: 0.3.4

        """
        colorspace_type_index = library.MagickGetImageColorspace(self.wand)
        if not colorspace_type_index:  # pragma: no cover
            self.raise_exception()
        return COLORSPACE_TYPES[text(colorspace_type_index)]

    @colorspace.setter
    @manipulative
    def colorspace(self, colorspace_type):
        assertions.string_in_list(COLORSPACE_TYPES,
                                  'wand.image.COLORSPACE_TYPES',
                                  colorspace=colorspace_type)
        r = library.MagickSetImageColorspace(
            self.wand,
            COLORSPACE_TYPES.index(colorspace_type)
        )
        if not r:  # pragma: no cover
            self.raise_exception()

    @property
    def compose(self):
        """(:class:`basestring`) The type of image compose.
        It's a string from :const:`COMPOSITE_OPERATORS` list.
        It also can be set.

        .. versionadded:: 0.5.1
        """
        compose_index = library.MagickGetImageCompose(self.wand)
        return COMPOSITE_OPERATORS[compose_index]

    @compose.setter
    def compose(self, operator):
        assertions.string_in_list(COMPOSITE_OPERATORS,
                                  'wand.image.COMPOSITE_OPERATORS',
                                  compose=operator)
        library.MagickSetImageCompose(self.wand,
                                      COMPOSITE_OPERATORS.index(operator))

    @property
    def compression(self):
        """(:class:`basestring`) The type of image compression.
        It's a string from :const:`COMPRESSION_TYPES` list.
        It also can be set.

        .. versionadded:: 0.3.6
        .. versionchanged:: 0.5.2
           Setting :attr:`compression` now sets both `image_info`
           and `images` in the internal image stack.
        """
        compression_index = library.MagickGetImageCompression(self.wand)
        return COMPRESSION_TYPES[compression_index]

    @compression.setter
    def compression(self, value):
        assertions.string_in_list(COMPRESSION_TYPES,
                                  'wand.image.COMPRESSION_TYPES',
                                  compression=value)
        library.MagickSetCompression(
            self.wand,
            COMPRESSION_TYPES.index(value)
        )
        library.MagickSetImageCompression(
            self.wand,
            COMPRESSION_TYPES.index(value)
        )

    @property
    def compression_quality(self):
        """(:class:`numbers.Integral`) Compression quality of this image.

        .. versionadded:: 0.2.0
        .. versionchanged:: 0.5.2
           Setting :attr:`compression_quality` now sets both `image_info`
           and `images` in the internal image stack.
        """
        return library.MagickGetImageCompressionQuality(self.wand)

    @compression_quality.setter
    @manipulative
    def compression_quality(self, quality):
        """Set compression quality for the image.

        :param quality: new compression quality setting
        :type quality: :class:`numbers.Integral`

        """
        assertions.assert_integer(compression_quality=quality)
        library.MagickSetCompressionQuality(self.wand, quality)
        r = library.MagickSetImageCompressionQuality(self.wand, quality)
        if not r:  # pragma: no cover
            raise ValueError('Unable to set compression quality to ' +
                             repr(quality))

    @property
    def depth(self):
        """(:class:`numbers.Integral`) The depth of this image.

        .. versionadded:: 0.2.1

        """
        return library.MagickGetImageDepth(self.wand)

    @depth.setter
    @manipulative
    def depth(self, depth):
        r = library.MagickSetImageDepth(self.wand, depth)
        if not r:  # pragma: no cover
            raise self.raise_exception()

    @property
    def dispose(self):
        """(:class:`basestring`) Controls how the image data is
        handled during animations. Values are from :const:`DISPOSE_TYPES`
        list, and can also be set.

        .. seealso::

            `Dispose Images`__ section in ``Animation Basics`` article.

        __ https://www.imagemagick.org/Usage/anim_basics/#dispose_images

        .. versionadded:: 0.5.0
        """
        dispose_idx = library.MagickGetImageDispose(self.wand)
        try:
            return DISPOSE_TYPES[dispose_idx]
        except IndexError:  # pragma: no cover
            return DISPOSE_TYPES[0]

    @dispose.setter
    def dispose(self, value):
        assertions.string_in_list(DISPOSE_TYPES,
                                  'wand.image.DISPOSE_TYPES',
                                  dispose=value)
        library.MagickSetImageDispose(self.wand, DISPOSE_TYPES.index(value))

    @property
    def font(self):
        """(:class:`wand.font.Font`) The current font options."""
        if not self.font_path:
            return None
        return Font(
            path=text(self.font_path),
            size=self.font_size,
            color=self.font_color,
            antialias=self.antialias,
            stroke_color=self.stroke_color,
            stroke_width=self.stroke_width
        )

    @font.setter
    @manipulative
    def font(self, font):
        if not isinstance(font, Font):
            raise TypeError('font must be a wand.font.Font, not ' + repr(font))
        self.font_path = font.path
        self.font_size = font.size
        self.font_color = font.color
        self.antialias = font.antialias
        if font.stroke_color:
            self.stroke_color = font.stroke_color
        if font.stroke_width is not None:
            self.stroke_width = font.stroke_width

    @property
    def font_antialias(self):
        """
        .. deprecated:: 0.5.0
           Use :attr:`antialias` instead.
        """
        return self.antialias

    @font_antialias.setter
    def font_antialias(self, antialias):
        self.antialias = antialias

    @property
    def font_color(self):
        return Color(self.options['fill'])

    @font_color.setter
    @manipulative
    def font_color(self, color):
        if isinstance(color, string_type):
            color = Color(color)
        assertions.assert_color(font_color=color)
        self.options['fill'] = color.string

    @property
    def font_path(self):
        """(:class:`basestring`) The path of the current font.
        It also can be set.

        """
        return text(library.MagickGetFont(self.wand))

    @font_path.setter
    @manipulative
    def font_path(self, font):
        font = binary(font)
        r = library.MagickSetFont(self.wand, font)
        if not r:  # pragma: no cover
            self.raise_exception()

    @property
    def font_size(self):
        """(:class:`numbers.Real`) The font size.  It also can be set."""
        return library.MagickGetPointsize(self.wand)

    @font_size.setter
    @manipulative
    def font_size(self, size):
        assertions.assert_real(font_size=size)
        if size < 0.0:
            raise ValueError('cannot be less then 0.0, but got ' + repr(size))
        r = library.MagickSetPointsize(self.wand, size)
        if not r:  # pragma: no cover
            self.raise_exception()

    @property
    def format(self):
        """(:class:`basestring`) The image format.

        If you want to convert the image format, just reset this property::

            assert isinstance(img, wand.image.Image)
            img.format = 'png'

        It may raise :exc:`ValueError` when the format is unsupported.

        .. seealso::

           `ImageMagick Image Formats`__
              ImageMagick uses an ASCII string known as *magick* (e.g. ``GIF``)
              to identify file formats, algorithms acting as formats,
              built-in patterns, and embedded profile types.

           __ http://www.imagemagick.org/script/formats.php

        .. versionadded:: 0.1.6

        """
        fmt = library.MagickGetImageFormat(self.wand)
        if bool(fmt):
            return text(fmt.value)
        else:  # pragma: no cover
            self.raise_exception()

    @format.setter
    def format(self, fmt):
        assertions.assert_string(format=fmt)
        fmt = fmt.strip()
        r = library.MagickSetImageFormat(self.wand, binary(fmt.upper()))
        if not r:
            raise ValueError(repr(fmt) + ' is unsupported format')
        r = library.MagickSetFilename(self.wand,
                                      b'buffer.' + binary(fmt.lower()))
        if not r:  # pragma: no cover
            self.raise_exception()

    @property
    def fuzz(self):
        """(:class:`numbers.Real`) The normalized real number between ``0.0``
        and :attr:`quantum_range`. This property influences the accuracy of
        :meth:`compare()`.

        .. versionadded:: 0.5.3
        """
        return library.MagickGetImageFuzz(self.wand)

    @fuzz.setter
    def fuzz(self, value):
        assertions.assert_real(fuzz=value)
        library.MagickSetImageFuzz(self.wand, value)

    @property
    def gravity(self):
        """(:class:`basestring`) The text placement gravity used when
        annotating with text.  It's a string from :const:`GRAVITY_TYPES`
        list.  It also can be set.

        """
        gravity_index = library.MagickGetGravity(self.wand)
        if not gravity_index:  # pragma: no cover
            self.raise_exception()
        return GRAVITY_TYPES[gravity_index]

    @gravity.setter
    @manipulative
    def gravity(self, value):
        assertions.string_in_list(GRAVITY_TYPES,
                                  'wand.image.GRAVITY_TYPES',
                                  gravity=value)
        library.MagickSetGravity(self.wand, GRAVITY_TYPES.index(value))

    @property
    def green_primary(self):
        """(:class:`tuple`) The chromatic green primary point for the image.
        With ImageMagick-6 the primary value is ``(x, y)`` coordinates;
        however, ImageMagick-7 has ``(x, y, z)``.

        .. versionadded:: 0.5.2
        """
        x = ctypes.c_double(0.0)
        y = ctypes.c_double(0.0)
        r = None
        p = None
        if MAGICK_VERSION_NUMBER < 0x700:
            r = library.MagickGetImageGreenPrimary(self.wand, x, y)
            p = (x.value, y.value)
        else:  # pragma: no cover
            z = ctypes.c_double(0.0)
            r = library.MagickGetImageGreenPrimary(self.wand, x, y, z)
            p = (x.value, y.value, z.value)
        if not r:  # pragma: no cover
            self.raise_exception()
        return p

    @green_primary.setter
    def green_primary(self, coordinates):
        r = None
        if not isinstance(coordinates, abc.Sequence):
            raise TypeError('Primary must be a tuple')
        if MAGICK_VERSION_NUMBER < 0x700:
            x, y = coordinates
            r = library.MagickSetImageGreenPrimary(self.wand, x, y)
        else:  # pragma: no cover
            x, y, z = coordinates
            r = library.MagickSetImageGreenPrimary(self.wand, x, y, z)
        if not r:  # pragma: no cover
            self.raise_exception()

    @property
    def height(self):
        """(:class:`numbers.Integral`) The height of this image."""
        return library.MagickGetImageHeight(self.wand)

    @height.setter
    @manipulative
    def height(self, height):
        assertions.assert_unsigned_integer(height=height)
        library.MagickSetSize(self.wand, self.width, height)

    @property
    def histogram(self):
        """(:class:`HistogramDict`) The mapping that represents the histogram.
        Keys are :class:`~wand.color.Color` objects, and values are
        the number of pixels.

        .. tip::

            True-color photos can have millions of color values. If performance
            is more valuable than accuracy, remember to :meth:`quantize` the
            image before generating a :class:`HistogramDict`.

                with Image(filename='hd_photo.jpg') as img:
                    img.quantize(255, 'RGB', 0, False, False)
                    hist = img.histogram

        .. versionadded:: 0.3.0

        """
        return HistogramDict(self)

    @property
    def interlace_scheme(self):
        """(:class:`basestring`) The interlace used by the image.
        See :const:`INTERLACE_TYPES`.

        .. versionadded:: 0.5.2
        """
        scheme_idx = library.MagickGetInterlaceScheme(self.wand)
        return INTERLACE_TYPES[scheme_idx]

    @interlace_scheme.setter
    def interlace_scheme(self, scheme):
        assertions.string_in_list(INTERLACE_TYPES,
                                  'wand.image.INTERLACE_TYPES',
                                  interlace_scheme=scheme)
        scheme_idx = INTERLACE_TYPES.index(scheme)
        library.MagickSetInterlaceScheme(self.wand, scheme_idx)

    @property
    def interpolate_method(self):
        """(:class:`basestring`) The interpolation method of the image.
        See :const:`PIXEL_INTERPOLATE_METHODS`.

        .. versionadded:: 0.5.2
        """
        method_idx = library.MagickGetImageInterpolateMethod(self.wand)
        return PIXEL_INTERPOLATE_METHODS[method_idx]

    @interpolate_method.setter
    def interpolate_method(self, method):
        assertions.string_in_list(PIXEL_INTERPOLATE_METHODS,
                                  'wand.image.PIXEL_INTERPOLATE_METHODS',
                                  interpolate_method=method)
        method_idx = PIXEL_INTERPOLATE_METHODS.index(method)
        library.MagickSetImageInterpolateMethod(self.wand, method_idx)

    @property
    def kurtosis(self):
        """(:class:`numbers.Real`) The kurtosis of the image.

        .. tip::

            If you want both :attr:`kurtosis` & :attr:`skewness`, it
            would be faster to call :meth:`kurtosis_channel()` directly.

        .. versionadded:: 0.5.3
        """
        k, _ = self.kurtosis_channel()
        return k

    @property
    def length_of_bytes(self):
        """(:class:`numbers.Integral`) The original size, in bytes,
        of the image read. This will return `0` if the image was modified in
        a way that would invalidate the original length value.

        .. versionadded:: 0.5.4
        """
        size_ptr = ctypes.c_size_t(0)
        library.MagickGetImageLength(self.wand, ctypes.byref(size_ptr))
        return size_ptr.value

    @property
    def loop(self):
        """(:class:`numbers.Integral`) Number of frame iterations.
        A value of ``0`` will loop forever."""
        return library.MagickGetImageIterations(self.wand)

    @loop.setter
    def loop(self, iterations):
        assertions.assert_unsigned_integer(loop=iterations)
        library.MagickSetImageIterations(self.wand, iterations)

    @property
    def matte_color(self):
        """(:class:`wand.color.Color`) The color value of the matte channel.
        This can also be set.

        .. versionadded:: 0.4.1
        """
        pixel = library.NewPixelWand()
        result = library.MagickGetImageMatteColor(self.wand, pixel)
        if result:
            color = Color.from_pixelwand(pixel)
            pixel = library.DestroyPixelWand(pixel)
            return color
        else:  # pragma: no cover
            self.raise_exception()

    @matte_color.setter
    @manipulative
    def matte_color(self, color):
        if isinstance(color, string_type):
            color = Color(color)
        assertions.assert_color(matte_color=color)
        with color:
            result = library.MagickSetImageMatteColor(self.wand,
                                                      color.resource)
            if not result:  # pragma: no cover
                self.raise_exception()

    @property
    def maxima(self):
        """(:class:`numbers.Real`) The maximum quantum value within the image.
        Value between 0.0 and :attr:`quantum_range`

        .. tip::

            If you want both :attr:`maxima` & :attr:`minima`,
            it would be faster to call :meth:`range_channel()` directly.

        .. versionadded:: 0.5.3
        """
        _, max_q = self.range_channel()
        return max_q

    @property
    def mean(self):
        """(:class:`numbers.Real`) The mean of the image, and have a value
        between 0.0 and :attr:`quantum_range`

        .. tip::

            If you want both :attr:`mean` & :attr:`standard_deviation`, it
            would be faster to call :meth:`mean_channel()` directly.

        .. versionadded:: 0.5.3
        """
        m, _ = self.mean_channel()
        return m

    @property
    def minima(self):
        """(:class:`numbers.Real`) The minimum quantum value within the image.
        Value between 0.0 and :attr:`quantum_range`

        .. tip::

            If you want both :attr:`maxima` & :attr:`minima`,
            it would be faster to call :meth:`range_channel()` directly.

        .. versionadded:: 0.5.3
        """
        min_q, _ = self.range_channel()
        return min_q

    @property
    def orientation(self):
        """(:class:`basestring`) The image orientation.  It's a string from
        :const:`ORIENTATION_TYPES` list.  It also can be set.

        .. versionadded:: 0.3.0

        """
        orientation_index = library.MagickGetImageOrientation(self.wand)
        try:
            return ORIENTATION_TYPES[orientation_index]
        except IndexError:  # pragma: no cover
            return ORIENTATION_TYPES[0]

    @orientation.setter
    @manipulative
    def orientation(self, value):
        assertions.string_in_list(ORIENTATION_TYPES,
                                  'wand.image.ORIENTATION_TYPES',
                                  orientation=value)
        index = ORIENTATION_TYPES.index(value)
        library.MagickSetImageOrientation(self.wand, index)

    @property
    def page(self):
        """The dimensions and offset of this Wand's page as a 4-tuple:
        ``(width, height, x, y)``.

        Note that since it is based on the virtual canvas, it may not equal the
        dimensions of an image. See the ImageMagick documentation on the
        virtual canvas for more information.

        .. versionadded:: 0.4.3

        """
        w = ctypes.c_uint()
        h = ctypes.c_uint()
        x = ctypes.c_int()
        y = ctypes.c_int()
        r = library.MagickGetImagePage(self.wand, w, h, x, y)
        if not r:  # pragma: no cover
            self.raise_exception()
        return int(w.value), int(h.value), int(x.value), int(y.value)

    @page.setter
    @manipulative
    def page(self, newpage):
        if isinstance(newpage, abc.Sequence):
            w, h, x, y = newpage
        else:
            raise TypeError("page layout must be 4-tuple")
        r = library.MagickSetImagePage(self.wand, w, h, x, y)
        if not r:  # pragma: no cover
            self.raise_exception()

    @property
    def page_height(self):
        """(:class:`numbers.Integral`) The height of the page for this wand.

        .. versionadded:: 0.4.3

        """
        return self.page[1]

    @page_height.setter
    @manipulative
    def page_height(self, height):
        newpage = list(self.page)
        newpage[1] = height
        self.page = newpage

    @property
    def page_width(self):
        """(:class:`numbers.Integral`) The width of the page for this wand.

        .. versionadded:: 0.4.3

        """
        return self.page[0]

    @page_width.setter
    @manipulative
    def page_width(self, width):
        newpage = list(self.page)
        newpage[0] = width
        self.page = newpage

    @property
    def page_x(self):
        """(:class:`numbers.Integral`) The X-offset of the page for this wand.

        .. versionadded:: 0.4.3

        """
        return self.page[2]

    @page_x.setter
    @manipulative
    def page_x(self, x):
        newpage = list(self.page)
        newpage[2] = x
        self.page = newpage

    @property
    def page_y(self):
        """(:class:`numbers.Integral`) The Y-offset of the page for this wand.

        .. versionadded:: 0.4.3

        """
        return self.page[3]

    @page_y.setter
    @manipulative
    def page_y(self, y):
        newpage = list(self.page)
        newpage[3] = y
        self.page = newpage

    @property
    def quantum_range(self):
        """(:class:`int`) The maxumim value of a color channel that is
        supported by the imagemagick library.

        .. versionadded:: 0.2.0

        """
        result = ctypes.c_size_t()
        library.MagickGetQuantumRange(ctypes.byref(result))
        return result.value

    @property
    def red_primary(self):
        """(:class:`tuple`) The chromatic red primary point for the image.
        With ImageMagick-6 the primary value is ``(x, y)`` coordinates;
        however, ImageMagick-7 has ``(x, y, z)``.

        .. versionadded:: 0.5.2
        """
        x = ctypes.c_double(0.0)
        y = ctypes.c_double(0.0)
        r = None
        p = None
        if MAGICK_VERSION_NUMBER < 0x700:
            r = library.MagickGetImageRedPrimary(self.wand, x, y)
            p = (x.value, y.value)
        else:  # pragma: no cover
            z = ctypes.c_double(0.0)
            r = library.MagickGetImageRedPrimary(self.wand, x, y, z)
            p = (x.value, y.value, z.value)
        if not r:  # pragma: no cover
            self.raise_exception()
        return p

    @red_primary.setter
    def red_primary(self, coordinates):
        r = None
        if not isinstance(coordinates, abc.Sequence):
            raise TypeError('Primary must be a tuple')
        if MAGICK_VERSION_NUMBER < 0x700:
            x, y = coordinates
            r = library.MagickSetImageRedPrimary(self.wand, x, y)
        else:  # pragma: no cover
            x, y, z = coordinates
            r = library.MagickSetImageRedPrimary(self.wand, x, y, z)
        if not r:  # pragma: no cover
            self.raise_exception()

    @property
    def rendering_intent(self):
        """(:class:`basestring`) PNG rendering intent. See
        :const:`RENDERING_INTENT_TYPES` for valid options.

        .. versionadded:: 0.5.4
        """
        ri_index = library.MagickGetImageRenderingIntent(self.wand)
        return RENDERING_INTENT_TYPES[ri_index]

    @rendering_intent.setter
    def rendering_intent(self, value):
        assertions.string_in_list(RENDERING_INTENT_TYPES,
                                  'wand.image.RENDERING_INTENT_TYPES',
                                  rendering_intent=value)
        ri_index = RENDERING_INTENT_TYPES.index(value)
        library.MagickSetImageRenderingIntent(self.wand, ri_index)

    @property
    def resolution(self):
        """(:class:`tuple`) Resolution of this image.

        .. versionadded:: 0.3.0

        """
        x = ctypes.c_double()
        y = ctypes.c_double()
        r = library.MagickGetImageResolution(self.wand, x, y)
        if not r:  # pragma: no cover
            self.raise_exception()
        return int(x.value), int(y.value)

    @resolution.setter
    @manipulative
    def resolution(self, geometry):
        if isinstance(geometry, abc.Sequence):
            x, y = geometry
        elif isinstance(geometry, numbers.Real):
            x, y = geometry, geometry
        else:
            raise TypeError('resolution must be a (x, y) pair or a float '
                            'of the same x/y')
        if self.size == (0, 0):
            r = library.MagickSetResolution(self.wand, x, y)
        else:
            r = library.MagickSetImageResolution(self.wand, x, y)
        if not r:  # pragma: no cover
            self.raise_exception()

    @property
    def seed(self):
        """(:class:`numbers.Integral`) The seed for random number generator.

        .. warning::

            This property is only available with ImageMagick 7.0.8-41, or
            greater.

        .. versionadded:: 0.5.5
        """
        return self._seed

    @seed.setter
    def seed(self, value):
        if library.MagickSetSeed is None:
            msg = 'Property requires ImageMagick version 7.0.8-41 or greater.'
            raise WandLibraryVersionError(msg)
        assertions.assert_unsigned_integer(seed=value)
        self._seed = value
        library.MagickSetSeed(self.wand, value)

    @property
    def scene(self):
        """(:class:`numbers.Integral`) The scene number of the current frame
        within an animated image.

        .. versionadded:: 0.5.4
        """
        return library.MagickGetImageScene(self.wand)

    @scene.setter
    def scene(self, value):
        assertions.assert_unsigned_integer(scene=value)
        library.MagickSetImageScene(self.wand, value)

    @property
    def signature(self):
        """(:class:`str`) The SHA-256 message digest for the image pixel
        stream.

        .. versionadded:: 0.1.9

        """
        signature = library.MagickGetImageSignature(self.wand)
        return text(signature.value)

    @property
    def size(self):
        """(:class:`tuple`) The pair of (:attr:`width`, :attr:`height`).

        .. note::

            When working with animations, or other layer-based image formats,
            the :attr:`width` & :attr:`height` properties are referencing the
            last frame read into the image stack. To get the :attr:`size`
            of the entire animated images, call
            :meth:`Image.coalesce() <wand.image.BaseImage.coalesce>` method
            immediately after reading the image.
        """
        return self.width, self.height

    @property
    def skewness(self):
        """(:class:`numbers.Real`) The skewness of the image.

        .. tip::

            If you want both :attr:`kurtosis` & :attr:`skewness`, it
            would be faster to call :meth:`kurtosis_channel()` directly.

        .. versionadded:: 0.5.3
        """
        _, s = self.kurtosis_channel()
        return s

    @property
    def standard_deviation(self):
        """(:class:`numbers.Real`) The standard deviation of the image.

        .. tip::

            If you want both :attr:`mean` & :attr:`standard_deviation`, it
            would be faster to call :meth:`mean_channel()` directly.

        .. versionadded:: 0.5.3
        """
        _, s = self.mean_channel()
        return s

    @property
    def stroke_color(self):
        stroke = self.options['stroke']
        return Color(stroke) if stroke else None

    @stroke_color.setter
    @manipulative
    def stroke_color(self, color):
        if isinstance(color, string_type):
            color = Color(color)
        if isinstance(color, Color):
            self.options['stroke'] = color.string
        elif color is None:
            del self.options['stroke']
        else:
            raise TypeError('stroke_color must be a wand.color.Color, not ' +
                            repr(color))

    @property
    def stroke_width(self):
        strokewidth = self.options['strokewidth']
        return float(strokewidth) if strokewidth else None

    @stroke_width.setter
    @manipulative
    def stroke_width(self, width):
        assertions.assert_real(stroke_width=width)
        self.options['strokewidth'] = str(width)

    @property
    def ticks_per_second(self):
        """(:class:`numbers.Integral`) Internal clock for animated images.
        .. versionadded:: 0.5.4
        """
        return library.MagickGetImageTicksPerSecond(self.wand)

    @ticks_per_second.setter
    def ticks_per_second(self, value):
        assertions.assert_unsigned_integer(ticks_per_second=value)
        r = library.MagickSetImageTicksPerSecond(self.wand, value)
        if not r:  # pragma: no cover
            self.raise_exception()

    @property
    def type(self):
        """(:class:`basestring`) The image type.

        Defines image type as in :const:`IMAGE_TYPES` enumeration.

        It may raise :exc:`ValueError` when the type is unknown.

        .. versionadded:: 0.2.2

        """
        image_type_index = library.MagickGetImageType(self.wand)
        if not image_type_index:  # pragma: no cover
            self.raise_exception()
        return IMAGE_TYPES[text(image_type_index)]

    @type.setter
    @manipulative
    def type(self, image_type):
        assertions.string_in_list(IMAGE_TYPES, 'wand.image.IMAGE_TYPES',
                                  type=image_type)
        r = library.MagickSetImageType(self.wand,
                                       IMAGE_TYPES.index(image_type))
        if not r:  # pragma: no cover
            self.raise_exception()

    @property
    def units(self):
        """(:class:`basestring`) The resolution units of this image."""
        r = library.MagickGetImageUnits(self.wand)
        return UNIT_TYPES[text(r)]

    @units.setter
    @manipulative
    def units(self, units):
        assertions.string_in_list(UNIT_TYPES, 'wand.image.UNIT_TYPES',
                                  units=units)
        r = library.MagickSetImageUnits(self.wand, UNIT_TYPES.index(units))
        if not r:  # pragma: no cover
            self.raise_exception()

    @property
    def virtual_pixel(self):
        """(:class:`basestring`) The virtual pixel of image.
        This can also be set with a value from :const:`VIRTUAL_PIXEL_METHOD`
        ... versionadded:: 0.4.1
        """
        method_index = library.MagickGetImageVirtualPixelMethod(self.wand)
        return VIRTUAL_PIXEL_METHOD[method_index]

    @virtual_pixel.setter
    def virtual_pixel(self, method):
        assertions.string_in_list(VIRTUAL_PIXEL_METHOD,
                                  'wand.image.VIRTUAL_PIXEL_METHOD',
                                  virtual_pixel=method)
        library.MagickSetImageVirtualPixelMethod(
            self.wand,
            VIRTUAL_PIXEL_METHOD.index(method)
        )

    @property
    def wand(self):
        """Internal pointer to the MagickWand instance. It may raise
        :exc:`ClosedImageError` when the instance has destroyed already.

        """
        try:
            return self.resource
        except DestroyedResourceError:
            raise ClosedImageError(repr(self) + ' is closed already')

    @wand.setter
    def wand(self, wand):
        try:
            self.resource = wand
        except TypeError:
            raise TypeError(repr(wand) + ' is not a MagickWand instance')

    @wand.deleter
    def wand(self):
        del self.resource

    @property
    def width(self):
        """(:class:`numbers.Integral`) The width of this image."""
        return library.MagickGetImageWidth(self.wand)

    @width.setter
    @manipulative
    def width(self, width):
        assertions.assert_unsigned_integer(width=width)
        library.MagickSetSize(self.wand, width, self.height)

    @property
    def white_point(self):
        """(:class:`tuple`) The chromatic white point for the image.
        With ImageMagick-6 the primary value is ``(x, y)`` coordinates;
        however, ImageMagick-7 has ``(x, y, z)``.

        .. versionadded:: 0.5.2
        """
        x = ctypes.c_double(0.0)
        y = ctypes.c_double(0.0)
        r = None
        p = None
        if MAGICK_VERSION_NUMBER < 0x700:
            r = library.MagickGetImageWhitePoint(self.wand, x, y)
            p = (x.value, y.value)
        else:  # pragma: no cover
            z = ctypes.c_double(0.0)
            r = library.MagickGetImageWhitePoint(self.wand, x, y, z)
            p = (x.value, y.value, z.value)
        if not r:  # pragma: no cover
            self.raise_exception()
        return p

    @white_point.setter
    def white_point(self, coordinates):
        r = None
        if not isinstance(coordinates, abc.Sequence):
            raise TypeError('Primary must be a tuple')
        if MAGICK_VERSION_NUMBER < 0x700:
            x, y = coordinates
            r = library.MagickSetImageWhitePoint(self.wand, x, y)
        else:  # pragma: no cover
            x, y, z = coordinates
            r = library.MagickSetImageWhitePoint(self.wand, x, y, z)
        if not r:  # pragma: no cover
            self.raise_exception()

    @manipulative
    def _auto_orient(self):
        """Fallback for :attr:`auto_orient()` method
        (which wraps :c:func:`MagickAutoOrientImage`),
        fixes orientation by checking EXIF data.

        .. versionadded:: 0.4.1

        """
        exif_orientation = self.metadata.get('exif:orientation')
        if not exif_orientation:
            return

        orientation_type = ORIENTATION_TYPES[int(exif_orientation)]

        fn_lookup = {
            'undefined': None,
            'top_left': None,
            'top_right': self.flop,
            'bottom_right': functools.partial(self.rotate, degree=180.0),
            'bottom_left': self.flip,
            'left_top': self.transpose,
            'right_top': functools.partial(self.rotate, degree=90.0),
            'right_bottom': self.transverse,
            'left_bottom': functools.partial(self.rotate, degree=270.0)
        }

        fn = fn_lookup.get(orientation_type)

        if not fn:
            return

        fn()
        self.orientation = 'top_left'

    def _channel_to_mask(self, value):
        """Attempts to resolve user input into a :c:type:`ChannelType` bit-mask.
        User input can be an integer, a string defined in :const:`CHANNELS`,
        or a string following ImageMagick's `CLI format`__.

        __ https://imagemagick.org/script/command-line-options.php#channel

        .. code::

            # User generated bit-mask.
            mask = self._channel_to_mask(CHANNELS['red'] | CHANNELS['green'])
            # Defined constant.
            mask = self._channel_to_mask('red')
            # CLI format.
            mask = self._channel_to_mask('RGB,Sync')

        :param value: Mixed user input.
        :type value: :class:`numbers.Integral` or :class:`basestring`
        :returns: Bit-mask constant.
        :rtype: :class:`numbers.Integral`

        .. versionadded:: 0.5.5
        """
        mask = -1
        if isinstance(value, numbers.Integral) and not isinstance(value, bool):
            mask = value
        elif isinstance(value, string_type):
            if value in CHANNELS:
                mask = CHANNELS[value]
            elif libmagick.ParseChannelOption:
                mask = libmagick.ParseChannelOption(binary(value))
        else:
            raise TypeError(repr(value) + ' is an invalid channel type'
                            '; see wand.image.CHANNELS dictionary')
        if mask < 0:
            raise ValueError('expected value from wand.image.CHANNELS, not '
                             + repr(value))
        return mask

    def _gravity_to_offset(self, gravity, width, height):
        """Calculate the top/left offset by a given gravity.

        Some methods in MagickWand's C-API do not respect gravity, but
        instead, expect a x/y offset. This is confusing to folks coming from
        the CLI documentation that does respect gravity

        :param gravity: Value from :const:`GRAVITY_TYPES`.
        :type gravity: :class:`basestring`
        :raises: :class:`ValueError` if gravity is no known.
        :returns: :class:`numbers.Intergal` top, :class:`numbers.Intergal` left

        .. versionadded:: 0.5.3
        """
        top, left = 0, 0
        assertions.string_in_list(GRAVITY_TYPES, 'wand.image.GRAVITY_TYPES',
                                  gravity=gravity)
        # Set `top` based on given gravity
        if gravity in ('north_west', 'north', 'north_east'):
            top = 0
        elif gravity in ('west', 'center', 'east'):
            top = int(self.height / 2) - int(height / 2)
        elif gravity in ('south_west', 'south', 'south_east'):
            top = self.height - height
        # Set `left` based on given gravity
        if gravity in ('north_west', 'west', 'south_west'):
            left = 0
        elif gravity in ('north', 'center', 'south'):
            left = int(self.width / 2) - int(width / 2)
        elif gravity in ('north_east', 'east', 'south_east'):
            left = self.width - width
        return top, left

    @manipulative
    @trap_exception
    def adaptive_blur(self, radius=0.0, sigma=0.0, channel=None):
        """Adaptively blurs the image by decreasing Gaussian as the operator
        approaches detected edges.

        :param radius: size of gaussian aperture.
        :type radius: :class:`numbers.Real`
        :param sigma: Standard deviation of the gaussian filter.
        :type sigma: :class:`numbers.Real`
        :param channel: Apply the blur effect on a specific channel.
                        See :const:`CHANNELS`.
        :type channel: :class:`basestring`

        .. versionadded:: 0.5.3

        .. versionchanged:: 0.5.5
           Added optional ``channel`` argument
        """
        assertions.assert_real(radius=radius, sigma=sigma)
        if channel is None:
            r = library.MagickAdaptiveBlurImage(self.wand, radius, sigma)
        else:
            channel_ch = self._channel_to_mask(channel)
            if MAGICK_VERSION_NUMBER < 0x700:
                r = library.MagickAdaptiveBlurImageChannel(self.wand,
                                                           channel_ch,
                                                           radius,
                                                           sigma)
            else:  # pragma: no cover
                mask = library.MagickSetImageChannelMask(self.wand,
                                                         channel_ch)
                r = library.MagickAdaptiveBlurImage(self.wand, radius, sigma)
                library.MagickSetImageChannelMask(self.wand, mask)
        return r

    @manipulative
    @trap_exception
    def adaptive_resize(self, columns=None, rows=None):
        """Adaptively resize image by applying Mesh interpolation.

        :param columns: width of resized image.
        :type columns: :class:`numbers.Integral`
        :param rows: hight of resized image.
        :type rows: :class:`numbers.Integral`

        .. versionadded:: 0.5.3
        """
        if columns is None:
            columns = self.width
        if rows is None:
            rows = self.height
        assertions.assert_integer(columns=columns, rows=rows)
        return library.MagickAdaptiveResizeImage(self.wand, columns, rows)

    @manipulative
    @trap_exception
    def adaptive_sharpen(self, radius=0.0, sigma=0.0, channel=None):
        """Adaptively sharpens the image by sharpening more intensely near
        image edges and less intensely far from edges.

        :param radius: size of gaussian aperture.
        :type radius: :class:`numbers.Real`
        :param sigma: Standard deviation of the gaussian filter.
        :type sigma: :class:`numbers.Real`
        :param channel: Apply the sharpen effect on a specific channel.
                        See :const:`CHANNELS`.
        :type channel: :class:`basestring`

        .. versionadded:: 0.5.3

        .. versionchanged:: 0.5.5
           Added optional ``channel`` argument
        """
        assertions.assert_real(radius=radius, sigma=sigma)
        if channel is None:
            r = library.MagickAdaptiveSharpenImage(self.wand, radius, sigma)
        else:
            channel_ch = self._channel_to_mask(channel)
            if MAGICK_VERSION_NUMBER < 0x700:
                r = library.MagickAdaptiveSharpenImageChannel(self.wand,
                                                              channel_ch,
                                                              radius,
                                                              sigma)
            else:  # pragma: no cover
                mask = library.MagickSetImageChannelMask(self.wand,
                                                         channel_ch)
                r = library.MagickAdaptiveSharpenImage(self.wand,
                                                       radius,
                                                       sigma)
                library.MagickSetImageChannelMask(self.wand, mask)
        return r

    @manipulative
    def adaptive_threshold(self, width, height, offset=0.0):
        """Applies threshold for each pixel based on neighboring pixel values.

        :param width: size of neighboring pixels on the X-axis.
        :type width: :class:`numbers.Integral`
        :param height: size of neighboring pixels on the Y-axis.
        :type height: :class:`numbers.Integral`
        :param offset: normalized number between `0.0` and
                       :attr:`quantum_range`. Forces the pixels to black if
                       values are below ``offset``.
        :type offset: :class:`numbers.Real`

        .. versionadded:: 0.5.3
        """
        assertions.assert_integer(width=width, height=height)
        assertions.assert_real(offset=offset)
        if MAGICK_VERSION_NUMBER < 0x700:
            offset = int(offset)
        return library.MagickAdaptiveThresholdImage(self.wand, width,
                                                    height, offset)

    @manipulative
    @trap_exception
    def auto_gamma(self):
        """Adjust the gamma level of an image.

        .. versionadded:: 0.5.4
        """
        return library.MagickAutoGammaImage(self.wand)

    @manipulative
    @trap_exception
    def auto_level(self):
        """Scale the minimum and maximum values to a full quantum range.

        .. versionadded:: 0.5.4
        """
        return library.MagickAutoLevelImage(self.wand)

    @manipulative
    @trap_exception
    def auto_orient(self):
        """Adjusts an image so that its orientation is suitable
        for viewing (i.e. top-left orientation). If available it uses
        :c:func:`MagickAutoOrientImage` (was added in ImageMagick 6.8.9+)
        if you have an older magick library,
        it will use :attr:`_auto_orient()` method for fallback.

        .. versionadded:: 0.4.1

        """
        try:
            return library.MagickAutoOrientImage(self.wand)
        except AttributeError:  # pragma: no cover
            self._auto_orient()
            return True

    @manipulative
    @trap_exception
    def auto_threshold(self, method='kapur'):
        """Automatically performs threshold method to reduce grayscale data
        down to a binary black & white image. Included algorithms are
        Kepur, Otsu, and Triangle methods.

        .. warning::

            This class method is only available with ImageMagick 7.0.8-41, or
            greater.

        :param method: Which threshold method to apply.
                       See :const:`AUTO_THRESHOLD_METHODS`.
                       Defaults to ``'kapur'``.
        :type method: :class:`basestring`
        :raises WandLibraryVersionError: if function is not available on
                                         system's library.

        .. versionadded:: 0.5.5
        """
        if library.MagickAutoThresholdImage is None:
            msg = 'Method requires ImageMagick version 7.0.8-41 or greater.'
            raise WandLibraryVersionError(msg)
        assertions.string_in_list(AUTO_THRESHOLD_METHODS,
                                  'wand.image.AUTO_THRESHOLD_METHODS',
                                  method=method)
        method_idx = AUTO_THRESHOLD_METHODS.index(method)
        return library.MagickAutoThresholdImage(self.wand, method_idx)

    @manipulative
    @trap_exception
    def black_threshold(self, threshold):
        """Forces all pixels above a given color as black. Leaves pixels
        above threshold unaltered.

        :param threshold: Color to be referenced as a threshold.
        :type threshold: :class:`Color`

        .. versionadded:: 0.5.3
        """
        if isinstance(threshold, string_type):
            threshold = Color(threshold)
        assertions.assert_color(threshold=threshold)
        with threshold:
            r = library.MagickBlackThresholdImage(self.wand,
                                                  threshold.resource)
        return r

    @manipulative
    @trap_exception
    def blue_shift(self, factor=1.5):
        """Mutes colors of the image by shifting blue values.

        :param factor: Amount to adjust values.
        :type factor: :class:`numbers.Real`

        .. versionadded:: 0.5.3
        """
        assertions.assert_real(factor=factor)
        return library.MagickBlueShiftImage(self.wand, factor)

    @manipulative
    @trap_exception
    def blur(self, radius, sigma, channel=None):
        """Blurs the image.  We convolve the image with a gaussian operator
        of the given ``radius`` and standard deviation (``sigma``).
        For reasonable results, the ``radius`` should be larger
        than ``sigma``.  Use a ``radius`` of 0 and :meth:`blur()` selects
        a suitable ``radius`` for you.

        :param radius: the radius of the, in pixels,
                       not counting the center pixel
        :type radius: :class:`numbers.Real`
        :param sigma: the standard deviation of the, in pixels
        :type sigma: :class:`numbers.Real`
        :param channel: Optional color channel to apply blur. See
                        :const:`CHANNELS`.
        :type channel: :class:`basestring`

        .. versionadded:: 0.4.5

        .. versionchanged:: 0.5.5
           Added optional ``channel`` argument.
        """
        assertions.assert_real(radius=radius, sigma=sigma)
        if channel is None:
            r = library.MagickBlurImage(self.wand, radius, sigma)
        else:
            channel_ch = self._channel_to_mask(channel)
            if MAGICK_VERSION_NUMBER < 0x700:
                r = library.MagickBlurImageChannel(self.wand,
                                                   channel_ch,
                                                   radius,
                                                   sigma)
            else:  # pragma: no cover
                mask = library.MagickSetImageChannelMask(self.wand, channel_ch)
                r = library.MagickBlurImage(self.wand, radius, sigma)
                library.MagickSetImageChannelMask(self.wand, mask)
        return r

    @trap_exception
    def border(self, color, width, height, compose="copy"):
        """Surrounds the image with a border.

        :param bordercolor: the border color pixel wand
        :type image: :class:`~wand.color.Color`
        :param width: the border width
        :type width: :class:`numbers.Integral`
        :param height: the border height
        :type height: :class:`numbers.Integral`
        :param compose: Use composite operator when applying frame. Only used
                        if called with ImageMagick 7+.
        :type compose: :class:`basestring`

        .. versionadded:: 0.3.0
        .. versionchanged:: 0.5.0
           Added ``compose`` paramater, and ImageMagick 7 support.
        """
        if isinstance(color, string_type):
            color = Color(color)
        assertions.assert_color(color=color)
        with color:
            if MAGICK_VERSION_NUMBER < 0x700:
                result = library.MagickBorderImage(self.wand, color.resource,
                                                   width, height)
            else:  # pragma: no cover
                assertions.string_in_list(COMPOSITE_OPERATORS,
                                          'wand.image.COMPOSITE_OPERATORS',
                                          compose=compose)
                compose_idx = COMPOSITE_OPERATORS.index(compose)
                result = library.MagickBorderImage(self.wand, color.resource,
                                                   width, height, compose_idx)
        return result

    @manipulative
    @trap_exception
    def brightness_contrast(self, brightness=0.0, contrast=0.0, channel=None):
        """Converts ``brightness`` & ``contrast`` paramaters into a slope &
        intercept, and applies a polynomial function.

        :param brightness: between ``-100.0`` and ``100.0``. Default is ``0.0``
                           for unchanged.
        :type brightness: :class:`numbers.Real`
        :param contrast: between ``-100.0`` and ``100.0``. Default is ``0.0``
                         for unchanged.
        :type contrast: :class:`numbers.Real`
        :param channel: Isolate a single color channel to apply contrast.
                        See :const:`CHANNELS`.

        .. versionadded:: 0.5.4

        .. versionchanged:: 0.5.5
           Optional ``channel`` argument added.
        """
        assertions.assert_real(brightness=brightness, contrast=contrast)
        if channel is None:
            r = library.MagickBrightnessContrastImage(self.wand,
                                                      brightness,
                                                      contrast)
        else:
            channel_ch = self._channel_to_mask(channel)
            if MAGICK_VERSION_NUMBER < 0x700:
                r = library.MagickBrightnessContrastImageChannel(self.wand,
                                                                 channel_ch,
                                                                 brightness,
                                                                 contrast)
            else:  # pragma: no cover
                mask = library.MagickSetImageChannelMask(self.wand, channel_ch)
                r = library.MagickBrightnessContrastImage(self.wand,
                                                          brightness,
                                                          contrast)
                library.MagickSetImageChannelMask(self.wand, mask)
        return r

    @manipulative
    @trap_exception
    def canny(self, radius=0.0, sigma=1.0, lower_percent=0.1,
              upper_percent=0.3):
        """Detect edges by leveraging a multi-stage Canny algorithm.

        .. warning::

            This class method is only available with ImageMagick 7.0.8-41, or
            greater.

        :param radius: Size of gaussian filter.
        :type radius: :class:`numbers.Real`
        :param sigma: Standard deviation of gaussian filter.
        :type sigma: :class:`numbers.Real`
        :param lower_percent: Normalized lower threshold.
        :type lower_percent: :class:`numbers.Real`
        :param upper_percent: Normalized upper threshold.
        :type upper_percent: :class:`numbers.Real`
        :raises WandLibraryVersionError: if function is not available on
                                         system's library.
        """
        if library.MagickCannyEdgeImage is None:
            msg = 'Method requires ImageMagick version 7.0.8-41 or greater.'
            raise WandLibraryVersionError(msg)
        assertions.assert_real(radius=radius, sigma=sigma,
                               lower_percent=lower_percent,
                               upper_percent=upper_percent)
        return library.MagickCannyEdgeImage(self.wand, radius, sigma,
                                            lower_percent, upper_percent)

    @manipulative
    def concat(self, stacked=False):
        """Concatenates images in stack into a single image. Left-to-right
        by default, top-to-bottom if ``stacked`` is True.

        :param stacked: stack images in a column, or in a row (default)
        :type stacked: :class:`bool`

        .. versionadded:: 0.5.0
        """
        assertions.assert_bool(stacked=stacked)
        r = library.MagickAppendImages(self.wand, stacked)
        if not r:  # pragma: no cover
            self.raise_exception()
        self.wand = r

    @manipulative
    def caption(self, text, left=0, top=0, width=None, height=None, font=None,
                gravity=None):
        """Writes a caption ``text`` into the position.

        :param text: text to write
        :type text: :class:`basestring`
        :param left: x offset in pixels
        :type left: :class:`numbers.Integral`
        :param top: y offset in pixels
        :type top: :class:`numbers.Integral`
        :param width: width of caption in pixels.
                      default is :attr:`width` of the image
        :type width: :class:`numbers.Integral`
        :param height: height of caption in pixels.
                       default is :attr:`height` of the image
        :type height: :class:`numbers.Integral`
        :param font: font to use.  default is :attr:`font` of the image
        :type font: :class:`wand.font.Font`
        :param gravity: text placement gravity.
                        uses the current :attr:`gravity` setting of the image
                        by default
        :type gravity: :class:`basestring`

        .. versionadded:: 0.3.0

        """
        assertions.assert_integer(left=left, top=top)
        if font is not None and not isinstance(font, Font):
            raise TypeError('font must be a wand.font.Font, not ' + repr(font))
        if gravity is not None:
            assertions.string_in_list(GRAVITY_TYPES,
                                      'wand.image.GRAVITY_TYPES',
                                      gravity=gravity)
        if width is None:
            width = self.width - left
        else:
            assertions.assert_integer(width=width)
        if height is None:
            height = self.height - top
        else:
            assertions.assert_integer(height=height)
        if not font:
            try:
                font = self.font
            except TypeError:
                raise TypeError('font must be specified or existing in image')
        with Image() as textboard:
            library.MagickSetSize(textboard.wand, width, height)
            textboard.font = font
            textboard.gravity = gravity or self.gravity
            with Color('transparent') as background_color:
                library.MagickSetBackgroundColor(textboard.wand,
                                                 background_color.resource)
            textboard.read(filename=b'caption:' + text.encode('utf-8'))
            self.composite(textboard, left, top)

    @trap_exception
    def charcoal(self, radius, sigma):
        """Transform an image into a simulated charcoal drawing.

        :param radius: The size of the Gaussian operator.
        :type radius: :class:`numbers.Real`
        :param sigma: The standard deviation of the Gaussian.
        :type sigma: :class:`numbers.Real`

        .. versionadded:: 0.5.3
        """
        assertions.assert_real(radius=radius, sigma=sigma)
        return library.MagickCharcoalImage(self.wand, radius, sigma)

    @manipulative
    @trap_exception
    def chop(self, width, height, x=0, y=0):
        """Removes a region of an image, and reduces the image size
        accordingly.

        :param width: Size of region.
        :type width: :class:`numbers.Integral`
        :param height: Size of region.
        :type height: :class:`numbers.Integral`
        :param x: Offset on the X-axis.
        :type x: :class:`numbers.Integral`
        :param y: Offset on the Y-axis.
        :type y: :class:`numbers.Integral`

        .. versionadded:: 0.5.5
        """
        assertions.assert_unsigned_integer(width=width, height=height)
        assertions.assert_integer(x=x, y=y)
        return library.MagickChopImage(self.wand, width, height, x, y)

    @manipulative
    @trap_exception
    def clahe(self, width, height, number_bins, clip_limit):
        """Contrast limited adaptive histogram equalization.

        .. warning::

            The CLAHE method is only available with ImageMagick-7.

        :param width: Tile division width.
        :type width: :class:`numbers.Integral`
        :param height: Tile division height.
        :type height: :class:`numbers.Integral`
        :param number_bins: Histogram bins.
        :type number_bins: :class:`numbers.Real`
        :param clip_limit: contrast limit.
        :type clip_limit: :class:`numbers.Real`
        :raises WandLibraryVersionError: If system's version of ImageMagick
                                         does not support this method.

        .. versionadded:: 0.5.5
        """
        if library.MagickCLAHEImage is None:
            msg = 'CLAHE method not defined in ImageMagick library.'
            raise WandLibraryVersionError(msg)
        assertions.assert_unsigned_integer(width=width, height=height)
        assertions.assert_real(number_bins=number_bins, clip_limit=clip_limit)
        return library.MagickCLAHEImage(self.wand, width, height,
                                        number_bins, clip_limit)

    @trap_exception
    def clamp(self, channel=None):
        """Restrict color values between 0 and quantum range. This is useful
        when applying arithmetic operations that could result in color values
        over/under-flowing.

        :param channel: Optional color channel.
        :type channel: :class:`basestring`

        .. versionadded:: 0.5.0

        .. versionchanged:: 0.5.5
           Added ``channel`` argument.
        """
        if channel is None:
            r = library.MagickClampImage(self.wand)
        else:
            channel_ch = self._channel_to_mask(channel)
            if MAGICK_VERSION_NUMBER < 0x700:
                r = library.MagickClampImageChannel(self.wand, channel_ch)
            else:  # pragma: no cover
                mask = library.MagickSetImageChannelMask(self.wand, channel_ch)
                r = library.MagickClampImage(self.wand)
                library.MagickSetImageChannelMask(self.wand, mask)
        return r

    def clone(self):
        """Clones the image. It is equivalent to call :class:`Image` with
        ``image`` parameter. ::

            with img.clone() as cloned:
                # manipulate the cloned image
                pass

        :returns: the cloned new image
        :rtype: :class:`Image`

        .. versionadded:: 0.1.1

        """
        return Image(image=self)

    @manipulative
    @trap_exception
    def clut(self, image, method='undefined', channel=None):
        """Replace color values by referencing another image as a Color
        Look Up Table.

        :param image: Color Look Up Table image.
        :type image: :class:`wand.image.BaseImage`
        :param method: Pixel Interpolate method. Only available with
                       ImageMagick-7. See :const:`PIXEL_INTERPOLATE_METHODS`
        :type method: :class:`basestring`
        :param channel: Optional color channel to target. See
                        :const:`CHANNELS`
        :type channel: :class:`basestring`

        .. versionadded:: 0.5.0

        .. versionchanged:: 0.5.5
           Added optional ``channel`` argument.
        """
        if not isinstance(image, BaseImage):
            raise TypeError('image must be a base image, not ' + repr(image))
        if MAGICK_VERSION_NUMBER < 0x700:
            if channel is None:
                r = library.MagickClutImage(self.wand, image.wand)
            else:
                channel_ch = self._channel_to_mask(channel)
                r = library.MagickClutImageChannel(self.wand,
                                                   channel_ch,
                                                   image.wand)
        else:  # pragma: no cover
            assertions.string_in_list(PIXEL_INTERPOLATE_METHODS,
                                      'wand.image.PIXEL_INTERPOLATE_METHODS',
                                      pixel_interpolate_method=method)
            method_idx = PIXEL_INTERPOLATE_METHODS.index(method)
            if channel is None:
                r = library.MagickClutImage(self.wand, image.wand, method_idx)
            else:
                channel_ch = self._channel_to_mask(channel)
                mask = library.MagickSetImageChannelMask(self.wand, channel_ch)
                r = library.MagickClutImage(self.wand, image.wand, method_idx)
                library.MagickSetImageChannelMask(self.wand, mask)
        return r

    @manipulative
    def coalesce(self):
        """Rebuilds image sequence with each frame size the same as first frame,
        and composites each frame atop of previous.

        .. note::

            Only affects GIF, and other formats with multiple pages/layers.

        .. versionadded:: 0.5.0
        """
        r = library.MagickCoalesceImages(self.wand)
        if not r:  # pragma: no cover
            self.raise_exception()
        self.wand = r

    def color_map(self, index, color=None):
        """Get & Set a color at a palette index. If ``color`` is given,
        the color at the index location will be set & returned. Omitting the
        ``color`` argument will only return the color value at index.

        Valid indexes are between ``0`` and total :attr:`colors` of the image.

        .. note::

            Ensure the image type is set to ``'palette'`` before calling the
            :meth:`color_map` method. For example::

                with Image(filename='graph.png') as img:
                    img.type = 'palette'
                    palette = [img.color_map(idx) for idx in range(img.colors)]
                    # ...

        :param index: The color postion of the image palette.
        :type index: :class:`numbers.Integral`
        :param color: Optional color to _set_ at the given index.
        :type color: :class:`wand.color.Color`
        :returns: Color at index.
        :rtype: :class:`wand.color.Color`

        .. versionadded:: 0.5.3
        """
        if not isinstance(index, numbers.Integral):
            raise TypeError('index most be an integer, not ' + repr(index))
        if index < 0 or index >= self.colors:
            raise ValueError('index is out of palette range')
        if color:
            if isinstance(color, string_type):
                color = Color(color)
            if not isinstance(color, Color):
                raise TypeError('expecting in instance of Color, not ' +
                                repr(color))
            with color:
                r = library.MagickSetImageColormapColor(self.wand,
                                                        index,
                                                        color.resource)
                if not r:  # pragma: no cover
                    self.raise_exception()
        else:
            color_ptr = library.NewPixelWand()
            r = library.MagickGetImageColormapColor(self.wand,
                                                    index,
                                                    color_ptr)
            if not r:
                color_ptr = library.DestroyPixelWand(color_ptr)
                self.raise_exception()
            color = Color.from_pixelwand(color_ptr)
            color_ptr = library.DestroyPixelWand(color_ptr)
        return color

    @manipulative
    @trap_exception
    def color_matrix(self, matrix):
        """Adjust color values by applying a matrix transform per pixel.

        Matrix should be given as 2D list, with a max size of 6x6::

            matrix = [
                [1.0, 0.0, 0.0],
                [0.0, 1.0, 0.0],
                [0.0, 0.0, 1.0],
            ]

        See `color-matrix`__ for examples.

        __ https://www.imagemagick.org/Usage/color_mods/#color-matrix

        :param matrix: 2D List of doubles.
        :type matrix: :class:`collections.abc.Sequence`

        .. versionadded:: 0.5.3
        """
        if not isinstance(matrix, abc.Sequence):
            raise TypeError('matrix must be a sequence, not ' + repr(matrix))
        rows = len(matrix)
        columns = None
        values = []
        for row in matrix:
            if not isinstance(row, abc.Sequence):
                raise TypeError('nested row must be a sequence, not ' +
                                repr(row))
            if columns is None:
                columns = len(row)
            elif columns != len(row):
                raise ValueError('rows have different column length')
            for column in row:
                values.append(str(column))
        kernel = binary('{0}x{1}:{2}'.format(columns,
                                             rows,
                                             ','.join(values)))
        exception_info = libmagick.AcquireExceptionInfo()
        if MAGICK_VERSION_NUMBER < 0x700:
            kernel_info = libmagick.AcquireKernelInfo(kernel)
        else:  # pragma: no cover
            kernel_info = libmagick.AcquireKernelInfo(kernel, exception_info)
        exception_info = libmagick.DestroyExceptionInfo(exception_info)
        r = library.MagickColorMatrixImage(self.wand, kernel_info)
        kernel_info = libmagick.DestroyKernelInfo(kernel_info)
        return r

    @manipulative
    @trap_exception
    def colorize(self, color=None, alpha=None):
        """Blends a given fill color over the image. The amount of blend is
        determined by the color channels given by the ``alpha`` argument.

        :param color: Color to paint image with.
        :type color: :class:`wand.color.Color`
        :param alpha: Defines how to blend color.
        :type alpha: :class:`wand.color.Color`

        .. versionadded:: 0.5.3
        """
        if isinstance(color, string_type):
            color = Color(color)
        if isinstance(alpha, string_type):
            alpha = Color(alpha)
        assertions.assert_color(color=color, alpha=alpha)
        with color:
            with alpha:
                r = library.MagickColorizeImage(self.wand,
                                                color.resource,
                                                alpha.resource)
        return r

    @manipulative
    def compare(self, image, metric='undefined', highlight=None,
                lowlight=None):
        """Compares an image to a reconstructed image.

        Set :attr:`fuzz` property to adjust pixel-compare thresholds.

        For example::

            from wand.image import Image

            with Image(filename='input.jpg') as base:
                with Image(filename='subject.jpg') as img:
                    base.fuzz = base.quantum_range * 0.20  # Threshold of 20%
                    result_image, result_metric = base.compare(img)
                    with result_image:
                        result_image.save(filename='diff.jpg')

        :param image: The reference image
        :type image: :class:`wand.image.Image`
        :param metric: The metric type to use for comparing. See
                       :const:`COMPARE_METRICS`
        :type metric: :class:`basestring`
        :param highlight: Set the color of the delta pixels in the resulting
                          difference image.
        :type highlight: :class:`~wand.color.Color` or :class:`basestring`
        :param lowlight: Set the color of the similar pixels in the resulting
                          difference image.
        :type lowlight: :class:`~wand.color.Color` or :class:`basestring`
        :returns: The difference image(:class:`wand.image.Image`),
                  the computed distortion between the images
                  (:class:`numbers.Integral`)
        :rtype: :class:`tuple`

        .. versionadded:: 0.4.3

        .. versionchanged:: 0.5.3
           Added support for ``highlight`` & ``lowlight``.
        """
        assertions.string_in_list(COMPARE_METRICS,
                                  'wand.image.COMPARE_METRICS',
                                  metric=metric)
        if highlight:
            if isinstance(highlight, Color):
                highlight = highlight.string
            library.MagickSetImageArtifact(self.wand,
                                           b'compare:highlight-color',
                                           binary(highlight))
        if lowlight:
            if isinstance(lowlight, Color):
                lowlight = lowlight.string
            library.MagickSetImageArtifact(self.wand,
                                           b'compare:lowlight-color',
                                           binary(lowlight))
        metric = COMPARE_METRICS.index(metric)
        distortion = ctypes.c_double()
        compared_image = library.MagickCompareImages(self.wand, image.wand,
                                                     metric,
                                                     ctypes.byref(distortion))
        return Image(BaseImage(compared_image)), distortion.value

    @manipulative
    def complex(self, operator='undefined', snr=None):
        """Performs `complex`_ mathematics against two images in a sequence,
        and generates a new image with two results.

        .. seealso::

            :meth:`forward_fourier_transform` &
            :meth:`inverse_fourier_transform`

        .. code::

            from wand.image import Image

            with Image(filename='real_part.png') as imgA:
                with Image(filename='imaginary_part.png') as imgB:
                    imgA.sequence.append(imgB)
                with imgA.complex('conjugate') as results:
                    results.save(filename='output-%02d.png')

        .. _complex: https://en.wikipedia.org/wiki/Complex_number

        .. warning::

            This class method is only available with ImageMagick 7.0.8-41, or
            greater.

        :param operator: Define which mathematic operator to perform. See
                         :const:`COMPLEX_OPERATORS`.
        :type operator: :class:`basestring`
        :param snr: Optional ``SNR`` parameter for ``'divide'`` operator.
        :type snr: :class:`basestring`
        :raises WandLibraryVersionError: If ImageMagick library does not
                                         support this function.

        .. versionadded:: 0.5.5
        """
        if library.MagickComplexImages is None:
            msg = 'Method requires ImageMagick version 7.0.8-41 or greater.'
            raise WandLibraryVersionError(msg)
        assertions.string_in_list(COMPLEX_OPERATORS,
                                  'wand.image.COMPLEX_OPERATORS',
                                  operator=operator)
        if snr is not None:
            self.artifacts['complex:snr=float'] = str(snr)
        operator_idx = COMPLEX_OPERATORS.index(operator)
        wand = library.MagickComplexImages(self.wand, operator_idx)
        if not bool(wand):
            self.raise_exception()
        return Image(BaseImage(wand))

    @trap_exception
    def composite(self, image, left=None, top=None, operator='over',
                  arguments=None, gravity=None):
        """Places the supplied ``image`` over the current image, with the top
        left corner of ``image`` at coordinates ``left``, ``top`` of the
        current image.  The dimensions of the current image are not changed.

        :param image: the image placed over the current image
        :type image: :class:`wand.image.Image`
        :param left: the x-coordinate where `image` will be placed
        :type left: :class:`numbers.Integral`
        :param top: the y-coordinate where `image` will be placed
        :type top: :class:`numbers.Integral`
        :param operator: the operator that affects how the composite
                         is applied to the image.  available values
                         can be found in the :const:`COMPOSITE_OPERATORS`
                         list. Default is ``'over'``.
        :type operator: :class:`basestring`
        :param arguments: Additional numbers given as a geometry string, or
                         comma delimited values. This is needed for
                         ``'blend'``, ``'displace'``, ``'dissolve'``, and
                         ``'modulate'`` operators.
        :type arguments: :class:`basestring`
        :param gravity: Calculate the ``top`` & ``left`` values based on
                        gravity value from :const:`GRAVITY_TYPES`.
        :type: gravity: :class:`basestring`

        .. versionadded:: 0.2.0

        .. versionchanged:: 0.5.3
           The operator can be set, as well as additional composite arguments.

        .. versionchanged:: 0.5.3
           Optional ``gravity`` argument was added.
        """
        if top is None and left is None:
            if gravity is None:
                gravity = self.gravity
            top, left = self._gravity_to_offset(gravity,
                                                image.width,
                                                image.height)
        elif gravity is not None:
            raise TypeError('Can not use gravity if top & left are given')
        elif top is None:
            top = 0
        elif left is None:
            left = 0
        assertions.assert_integer(left=left, top=top)
        try:
            op = COMPOSITE_OPERATORS.index(operator)
        except IndexError:
            raise ValueError(repr(operator) + ' is an invalid composite '
                             'operator type; see wand.image.COMPOSITE_'
                             'OPERATORS dictionary')
        if arguments:
            assertions.assert_string(arguments=arguments)
            r = library.MagickSetImageArtifact(image.wand,
                                               binary('compose:args'),
                                               binary(arguments))
            if not r:
                self.raise_exception()
            r = library.MagickSetImageArtifact(self.wand,
                                               binary('compose:args'),
                                               binary(arguments))
            if not r:  # pragma: no cover
                self.raise_exception()
        if MAGICK_VERSION_NUMBER < 0x700:
            r = library.MagickCompositeImage(self.wand, image.wand, op,
                                             int(left), int(top))
        else:  # pragma: no cover
            r = library.MagickCompositeImage(self.wand, image.wand, op, True,
                                             int(left), int(top))
        return r

    @manipulative
    @trap_exception
    def composite_channel(self, channel, image, operator, left=None, top=None,
                          arguments=None, gravity=None):
        """Composite two images using the particular ``channel``.

        :param channel: the channel type.  available values can be found
                        in the :const:`CHANNELS` mapping
        :param image: the composited source image.
                      (the receiver image becomes the destination)
        :type image: :class:`Image`
        :param operator: the operator that affects how the composite
                         is applied to the image.  available values
                         can be found in the :const:`COMPOSITE_OPERATORS`
                         list
        :type operator: :class:`basestring`
        :param left: the column offset of the composited source image
        :type left: :class:`numbers.Integral`
        :param top: the row offset of the composited source image
        :type top: :class:`numbers.Integral`
        :param arguments: Additional numbers given as a geometry string, or
                         comma delimited values. This is needed for
                         ``'blend'``, ``'displace'``, ``'dissolve'``, and
                         ``'modulate'`` operators.
        :type arguments: :class:`basestring`
        :param gravity: Calculate the ``top`` & ``left`` values based on
                        gravity value from :const:`GRAVITY_TYPES`.
        :type: gravity: :class:`basestring`
        :raises ValueError: when the given ``channel`` or
                            ``operator`` is invalid

        .. versionadded:: 0.3.0

        .. versionchanged:: 0.5.3
           Support for optional composite arguments has been added.

        .. versionchanged:: 0.5.3
           Optional ``gravity`` argument was added.
        """
        assertions.assert_string(operator=operator)
        ch_const = self._channel_to_mask(channel)
        if gravity:
            if left is None and top is None:
                top, left = self._gravity_to_offset(gravity,
                                                    image.width,
                                                    image.height)
            else:
                raise TypeError('Can not use gravity if top & left are given')
        if top is None:
            top = 0
        if left is None:
            left = 0
        assertions.assert_integer(left=left, top=top)
        try:
            op = COMPOSITE_OPERATORS.index(operator)
        except IndexError:
            raise IndexError(repr(operator) + ' is an invalid composite '
                             'operator type; see wand.image.COMPOSITE_'
                             'OPERATORS dictionary')
        if arguments:
            assertions.assert_string(arguments=arguments)
            library.MagickSetImageArtifact(image.wand,
                                           binary('compose:args'),
                                           binary(arguments))
            library.MagickSetImageArtifact(self.wand,
                                           binary('compose:args'),
                                           binary(arguments))
        if library.MagickCompositeImageChannel:
            r = library.MagickCompositeImageChannel(self.wand, ch_const,
                                                    image.wand, op, int(left),
                                                    int(top))
        else:  # pragma: no cover
            ch_mask = library.MagickSetImageChannelMask(self.wand, ch_const)
            r = library.MagickCompositeImage(self.wand, image.wand, op, True,
                                             int(left), int(top))
            library.MagickSetImageChannelMask(self.wand, ch_mask)
        return r

    def connected_components(self, connectivity=4, area_threshold=None):
        """Evaluates binary image, and groups connected pixels into objects.
        This method will also return a list of
        :class:`ConnectedComponentObject` instances that will describe an
        object's features.

        .. code::

            from wand.image import Image

            with Image(filename='objects.gif') as img:
                objects = img.connected_components()
            for cc_obj in objects:
                print("{0._id}: {0.size} {0.offset}".format(cc_obj))

            #=> 0: (256, 171) (0, 0)
            #=> 2: (120, 135) (104, 18)
            #=> 3: (50, 36) (129, 44)
            #=> 4: (21, 23) (0, 45)
            #=> 1: (4, 10) (252, 0)

        .. warning::

            This class method is only available with ImageMagick 7.0.8-41, or
            greater.

        .. tip::

            Set :attr:`fuzz` property to increase pixel matching by reducing
            tolerance of color-value comparisons::

                from wand.image import Image
                from wand.version import QUANTUM_RANGE

                with Image(filename='objects.gif') as img:
                    img.fuzz = 0.1 * QUANTUM_RANGE  # 10%
                    objects = img.connected_components()

        :param connectivity: Either ``4``, or ``8``. A value of ``4`` will
                            evaluate each pixels top-bottom, & left-right
                            neighbors. A value of ``8`` will use the same
                            pixels as with ``4``, but will also include the
                            four corners of each pixel.
        :type connectivity: :class:`numbers.Integral`
        :param area_threshold: Optional argument to exclude objects under an
                               area size.
        :type area_threshold: :class:`basestring`
        :returns: A list of :class:`ConnectedComponentObject`.
        :rtype: :class:`list` [:class:`ConnectedComponentObject`]
        :raises WandLibraryVersionError: If ImageMagick library
                                         does not support this method.

        .. versionadded:: 0.5.5
        """
        if library.MagickConnectedComponentsImage is None:
            msg = 'Method requires ImageMagick version 7.0.8-41 or greater.'
            raise WandLibraryVersionError(msg)
        if connectivity not in (4, 8):
            raise ValueError('connectivity must be 4, or 8.')
        if area_threshold is not None:
            key = 'connected-components:area-threshold'
            self.artifacts[key] = str(area_threshold)
        objects_ptr = ctypes.c_void_p(0)
        ccoi_mem_size = ctypes.sizeof(CCObjectInfo)
        r = library.MagickConnectedComponentsImage(self.wand, connectivity,
                                                   ctypes.byref(objects_ptr))
        objects = []
        if r and objects_ptr.value:
            for i in range(self.colors):
                temp = CCObjectInfo()
                src_addr = objects_ptr.value + (i * ccoi_mem_size)
                ctypes.memmove(ctypes.addressof(temp), src_addr, ccoi_mem_size)
                objects.append(ConnectedComponentObject(temp))
            objects_ptr = libmagick.RelinquishMagickMemory(objects_ptr)
        else:
            self.raise_exception()
        return objects

    @manipulative
    @trap_exception
    def contrast_stretch(self, black_point=0.0, white_point=None,
                         channel=None):
        """Enhance contrast of image by adjusting the span of the available
        colors.

        :param black_point: black point between 0.0 and 1.0.  default is 0.0
        :type black_point: :class:`numbers.Real`
        :param white_point: white point between 0.0 and 1.0.
                            Defaults to the same value given to the
                            ``black_point`` argument.
        :type white_point: :class:`numbers.Real`
        :param channel: optional color channel to apply contrast stretch
        :type channel: :const:`CHANNELS`
        :raises ValueError: if ``channel`` is not in :const:`CHANNELS`

        .. versionadded:: 0.4.1

        .. versionchanged:: 0.5.5
           The ``white_point`` argument will now default to the value given
           by the ``black_point`` argument.
        """
        assertions.assert_real(black_point=black_point)
        # If only black-point is given, match CLI behavior by
        # calculating white point
        if white_point is None:
            white_point = black_point
        assertions.assert_real(white_point=white_point)
        contrast_range = float(self.width * self.height)
        if 0.0 < black_point <= 1.0:
            black_point *= contrast_range
        if 0.0 < white_point <= 1.0:
            white_point *= contrast_range
        white_point = contrast_range - white_point
        if channel is None:
            r = library.MagickContrastStretchImage(self.wand,
                                                   black_point,
                                                   white_point)
        else:
            ch_const = self._channel_to_mask(channel)
            if library.MagickContrastStretchImageChannel:
                r = library.MagickContrastStretchImageChannel(self.wand,
                                                              ch_const,
                                                              black_point,
                                                              white_point)
            else:  # pragma: no cover
                # Set active channel, and capture mask to restore.
                channel_mask = library.MagickSetImageChannelMask(self.wand,
                                                                 ch_const)
                r = library.MagickContrastStretchImage(self.wand,
                                                       black_point,
                                                       white_point)
                # Restore original state of channels
                library.MagickSetImageChannelMask(self.wand, channel_mask)
        return r

    @manipulative
    @trap_exception
    def crop(self, left=0, top=0, right=None, bottom=None,
             width=None, height=None, reset_coords=True,
             gravity=None):
        """Crops the image in-place.

        .. sourcecode:: text

           +--------------------------------------------------+
           |              ^                         ^         |
           |              |                         |         |
           |             top                        |         |
           |              |                         |         |
           |              v                         |         |
           | <-- left --> +-------------------+  bottom       |
           |              |             ^     |     |         |
           |              | <-- width --|---> |     |         |
           |              |           height  |     |         |
           |              |             |     |     |         |
           |              |             v     |     |         |
           |              +-------------------+     v         |
           | <--------------- right ---------->               |
           +--------------------------------------------------+

        :param left: x-offset of the cropped image. default is 0
        :type left: :class:`numbers.Integral`
        :param top: y-offset of the cropped image. default is 0
        :type top: :class:`numbers.Integral`
        :param right: second x-offset of the cropped image.
                      default is the :attr:`width` of the image.
                      this parameter and ``width`` parameter are exclusive
                      each other
        :type right: :class:`numbers.Integral`
        :param bottom: second y-offset of the cropped image.
                       default is the :attr:`height` of the image.
                       this parameter and ``height`` parameter are exclusive
                       each other
        :type bottom: :class:`numbers.Integral`
        :param width: the :attr:`width` of the cropped image.
                      default is the :attr:`width` of the image.
                      this parameter and ``right`` parameter are exclusive
                      each other
        :type width: :class:`numbers.Integral`
        :param height: the :attr:`height` of the cropped image.
                       default is the :attr:`height` of the image.
                       this parameter and ``bottom`` parameter are exclusive
                       each other
        :type height: :class:`numbers.Integral`
        :param reset_coords:
           optional flag. If set, after the rotation, the coordinate frame
           will be relocated to the upper-left corner of the new image.
           By default is `True`.
        :type reset_coords: :class:`bool`
        :param gravity: optional flag. If set, will calculate the :attr:`top`
                        and :attr:`left` attributes. This requires both
                        :attr:`width` and :attr:`height` parameters to be
                        included.
        :type gravity: :const:`GRAVITY_TYPES`
        :raises ValueError: when one or more arguments are invalid

        .. note::

           If you want to crop the image but not in-place, use slicing
           operator.

        .. versionchanged:: 0.4.1
           Added ``gravity`` option. Using ``gravity`` along with
           ``width`` & ``height`` to auto-adjust ``left`` & ``top``
           attributes.

        .. versionchanged:: 0.1.8
           Made to raise :exc:`~exceptions.ValueError` instead of
           :exc:`~exceptions.IndexError` for invalid ``width``/``height``
           arguments.

        .. versionadded:: 0.1.7

        """
        if not (right is None or width is None):
            raise TypeError('parameters right and width are exclusive each '
                            'other; use one at a time')
        elif not (bottom is None or height is None):
            raise TypeError('parameters bottom and height are exclusive each '
                            'other; use one at a time')

        def abs_(n, m, null=None):
            if n is None:
                return m if null is None else null
            elif not isinstance(n, numbers.Integral):
                raise TypeError('expected integer, not ' + repr(n))
            elif n > m:
                raise ValueError(repr(n) + ' > ' + repr(m))
            return m + n if n < 0 else n

        # Define left & top if gravity is given.
        if gravity:
            if width is None or height is None:
                raise TypeError(
                    'both width and height must be defined with gravity'
                )
            top, left = self._gravity_to_offset(gravity, width, height)
        else:
            left = abs_(left, self.width, 0)
            top = abs_(top, self.height, 0)

        if width is None:
            right = abs_(right, self.width)
            width = right - left
        if height is None:
            bottom = abs_(bottom, self.height)
            height = bottom - top
        assertions.assert_counting_number(width=width, height=height)
        if (
            left == top == 0 and
            width == self.width and
            height == self.height
        ):
            return True
        if self.animation:
            self.wand = library.MagickCoalesceImages(self.wand)
            library.MagickSetLastIterator(self.wand)
            n = library.MagickGetIteratorIndex(self.wand)
            library.MagickResetIterator(self.wand)
            for i in xrange(0, n + 1):
                library.MagickSetIteratorIndex(self.wand, i)
                r = library.MagickCropImage(self.wand,
                                            width, height,
                                            left, top)
                if reset_coords:
                    self.reset_coords()
        else:
            r = library.MagickCropImage(self.wand, width, height, left, top)
            if reset_coords:
                self.reset_coords()
        return r

    @trap_exception
    def cycle_color_map(self, offset=1):
        """Shift the image color-map by a given offset.

        :param offset: number of steps to rotate index by.
        :type offset: :class:`numbers.Integral`

        .. versionadded:: 0.5.3
        """
        assertions.assert_integer(offset=offset)
        return library.MagickCycleColormapImage(self.wand, offset)

    @manipulative
    def deconstruct(self):
        """Iterates over internal image stack, and adjust each frame size to
        minimum bounding region of any changes from the previous frame.

        .. versionadded:: 0.5.0
        """
        r = library.MagickDeconstructImages(self.wand)
        if not r:
            self.raise_exception()
        self.wand = r

    @manipulative
    @trap_exception
    def deskew(self, threshold):
        """Attempts to remove skew artifacts common with most
        scanning & optical import devices.

        :params threshold: limit between foreground & background.
        :type threshold: :class:`numbers.Real`

        .. versionadded:: 0.5.0
        """
        assertions.assert_real(threshold=threshold)
        return library.MagickDeskewImage(self.wand, threshold)

    @manipulative
    @trap_exception
    def despeckle(self):
        """Applies filter to reduce noise in image.

        .. versionadded:: 0.5.0
        """
        return library.MagickDespeckleImage(self.wand)

    @manipulative
    @trap_exception
    def distort(self, method, arguments, best_fit=False):
        """Distorts an image using various distorting methods.

        .. code:: python

            from wand.image import Image
            from wand.color import Color

            with Image(filename='checks.png') as img:
                img.virtual_pixel = 'background'
                img.background_color = Color('green')
                img.matte_color = Color('skyblue')
                arguments = (0, 0, 20, 60,
                             90, 0, 70, 63,
                             0, 90, 5, 83,
                             90, 90, 85, 88)
                img.distort('perspective', arguments)
                img.save(filename='checks_perspective.png')

        .. image:: ../_images/wand/image/checks.png
        .. image:: ../_images/wand/image/checks_perspective.png

        Use :attr:`virtual_pixel`, :attr:`background_color`, and
        :attr:`matte_color` properties to control the behavior of pixels
        rendered outside of the image boundaries.

        Use :attr:`interpolate_method` to control how images scale-up.

        Distortion viewport, and scale, can be defined by using
        :attr:`Image.artifacts` dictionary. For example::

            img.artifacts['distort:viewport'] = '44x44+15+0'
            img.artifacts['distort:scale'] = '10'

        :param method: Distortion method name from :const:`DISTORTION_METHODS`
        :type method: :class:`basestring`
        :param arguments: List of distorting float arguments
                          unique to distortion method
        :type arguments: :class:`collections.abc.Sequence`
        :param best_fit: Attempt to resize resulting image fit distortion.
                         Defaults False
        :type best_fit: :class:`bool`

        .. versionadded:: 0.4.1
        """
        assertions.string_in_list(DISTORTION_METHODS,
                                  'wand.image.DISTORTION_METHODS',
                                  method=method)
        if not isinstance(arguments, abc.Sequence):
            raise TypeError('expected sequence of doubles, not ' +
                            repr(arguments))
        argc = len(arguments)
        argv = (ctypes.c_double * argc)(*arguments)
        method_idx = DISTORTION_METHODS.index(method)
        return library.MagickDistortImage(self.wand, method_idx,
                                          argc, argv, bool(best_fit))

    @manipulative
    @trap_exception
    def edge(self, radius=0.0):
        """Applies convolution filter to detect edges.

        :param radius: aperture of detection filter.
        :type radius: :class:`numbers.Real`

        .. versionadded:: 0.5.0
        """
        assertions.assert_real(radius=radius)
        return library.MagickEdgeImage(self.wand, radius)

    @manipulative
    @trap_exception
    def emboss(self, radius=0.0, sigma=0.0):
        """Applies convolution filter against gaussians filter.

        .. note::

            The `radius` value should be larger than `sigma` for best results.

        :param radius: filter aperture size.
        :type radius: :class:`numbers.Real`
        :param sigma: standard deviation.
        :type sigma: :class:`numbers.Real`

        .. versionadded:: 0.5.0
        """
        assertions.assert_real(radius=radius, sigma=sigma)
        return library.MagickEmbossImage(self.wand, radius, sigma)

    @manipulative
    @trap_exception
    def enhance(self):
        """Applies digital filter to reduce noise.

        .. versionadded:: 0.5.0
        """
        return library.MagickEnhanceImage(self.wand)

    @manipulative
    @trap_exception
    def equalize(self, channel=None):
        """Equalizes the image histogram

        :param channel: Optional channel. See :const:`CHANNELS`.
        :type channel: :class:`basestring`

        .. versionadded:: 0.3.10

        .. versionchanged:: 0.5.5
           Added optional ``channel`` argument.
        """
        if channel is None:
            r = library.MagickEqualizeImage(self.wand)
        else:
            channel_ch = self._channel_to_mask(channel)
            if MAGICK_VERSION_NUMBER < 0x700:
                r = library.MagickEqualizeImageChannel(self.wand, channel_ch)
            else:  # pragma: no cover
                mask = library.MagickSetImageChannelMask(self.wand, channel_ch)
                r = library.MagickEqualizeImage(self.wand)
                library.MagickSetImageChannelMask(self.wand, mask)
        return r

    @manipulative
    @trap_exception
    def evaluate(self, operator=None, value=0.0, channel=None):
        """Apply arithmetic, relational, or logical expression to an image.

        Percent values must be calculated against the quantum range of the
        image::

            fifty_percent = img.quantum_range * 0.5
            img.evaluate(operator='set', value=fifty_percent)

        :param operator: Type of operation to calculate
        :type operator: :const:`EVALUATE_OPS`
        :param value: Number to calculate with ``operator``
        :type value: :class:`numbers.Real`
        :param channel: Optional channel to apply operation on.
        :type channel: :const:`CHANNELS`
        :raises TypeError: When ``value`` is not numeric.
        :raises ValueError: When ``operator``, or ``channel`` are not defined
                            in constants.

        .. versionadded:: 0.4.1
        """
        assertions.string_in_list(EVALUATE_OPS, 'wand.image.EVALUATE_OPS',
                                  operator=operator)
        assertions.assert_real(value=value)
        idx_op = EVALUATE_OPS.index(operator)
        if channel is None:
            r = library.MagickEvaluateImage(self.wand, idx_op, value)
        else:
            ch_const = self._channel_to_mask(channel)
            # Use channel method if IM6, else create channel mask for IM7.
            if library.MagickEvaluateImageChannel:
                r = library.MagickEvaluateImageChannel(self.wand,
                                                       ch_const,
                                                       idx_op,
                                                       value)
            else:  # pragma: no cover
                # Set active channel, and capture mask to restore.
                channel_mask = library.MagickSetImageChannelMask(self.wand,
                                                                 ch_const)
                r = library.MagickEvaluateImage(self.wand, idx_op, value)
                # Restore original state of channels
                library.MagickSetImageChannelMask(self.wand, channel_mask)
        return r

    def export_pixels(self, x=0, y=0, width=None, height=None,
                      channel_map="RGBA", storage='char'):
        """Export pixel data from a raster image to
        a list of values.

        The ``channel_map`` tells ImageMagick which color
        channels to export, and what order they should be
        written as -- per pixel. Valid entries for
        ``channel_map`` are:

        - ``'R'`` - Red channel
        - ``'G'`` - Green channel
        - ``'B'`` - Blue channel
        - ``'A'`` - Alpha channel (``0`` is transparent)
        - ``'O'`` - Alpha channel (``0`` is opaque)
        - ``'C'`` - Cyan channel
        - ``'Y'`` - Yellow channel
        - ``'M'`` - Magenta channel
        - ``'K'`` - Black channel
        - ``'I'`` - Intensity channel (only for grayscale)
        - ``'P'`` - Padding

        See :const:`STORAGE_TYPES` for a list of valid
        ``storage`` options. This tells ImageMagick
        what type of data it should calculate & write to.
        For example; a storage type of ``'char'`` will write
        a 8-bit value between 0 ~ 255,  a storage type
        of ``'short'`` will write a 16-bit value between
        0 ~ 65535, and a ``'integer'`` will write a
        32-bit value between 0 ~ 4294967295.

        .. note::

            By default, the entire image will be exported
            as ``'char'`` storage with each pixel mapping
            Red, Green, Blue, & Alpha channels.


        :param x: horizontal starting coordinate of raster.
        :type x: :class:`numbers.Integral`
        :param y: vertical starting coordinate of raster.
        :type y: :class:`numbers.Integral`
        :param width: horizontal length of raster.
        :type width: :class:`numbers.Integral`
        :param height: vertical length of raster.
        :type height: :class:`numbers.Integral`
        :param channel_map: a string listing the channel data
                            format for each pixel.
        :type channel_map: :class:`basestring`
        :param storage: what data type each value should
                        be calculated as.
        :type storage: :class:`basestring`
        :returns: list of values.
        :rtype: :class:`collections.abc.Sequence`

        .. versionadded:: 0.5.0
        """
        _w, _h = self.size
        if width is None:
            width = _w
        if height is None:
            height = _h
        assertions.assert_integer(x=x, y=y, width=width, height=height)
        assertions.assert_string(channel_map=channel_map)
        assertions.string_in_list(STORAGE_TYPES, 'wand.image.STORAGE_TYPES',
                                  storage=storage)
        channel_map = channel_map.upper()
        valid_channels = 'RGBAOCYMKIP'
        for channel in channel_map:
            if channel not in valid_channels:
                raise ValueError('Unknown channel label: ' +
                                 repr(channel))
        c_storage_types = [
            None,
            ctypes.c_ubyte,
            ctypes.c_double,
            ctypes.c_float,
            ctypes.c_uint,
            ctypes.c_ulong,
            ctypes.c_double,  # FIXME: Might be c_longdouble?
            ctypes.c_ushort
        ]
        s_index = STORAGE_TYPES.index(storage)
        c_storage = c_storage_types[s_index]
        total_pixels = width * height
        c_buffer_size = total_pixels * len(channel_map)
        c_buffer = (c_buffer_size * c_storage)()
        r = library.MagickExportImagePixels(self.wand,
                                            x, y, width, height,
                                            binary(channel_map),
                                            s_index,
                                            ctypes.byref(c_buffer))
        if not r:  # pragma: no cover
            self.raise_exception()
        return c_buffer[:c_buffer_size]

    @manipulative
    @trap_exception
    def extent(self, width=None, height=None, x=0, y=0):
        """extends the image as defined by the geometry, gravity, and wand
        background color. Set the (x,y) offset of the geometry to move the
        original wand relative to the extended wand.

        :param width: the :attr:`width` of the extended image.
                      default is the :attr:`width` of the image.
        :type width: :class:`numbers.Integral`
        :param height: the :attr:`height` of the extended image.
                       default is the :attr:`height` of the image.
        :type height: :class:`numbers.Integral`
        :param x: the :attr:`x` offset of the extended image.
                      default is 0
        :type x: :class:`numbers.Integral`
        :param y: the :attr:`y` offset of the extended image.
                       default is 0
        :type y: :class:`numbers.Integral`

        .. versionadded:: 0.4.5
        """
        if width is None or width == 0:
            width = self.width
        if height is None or height == 0:
            height = self.height
        if width < 0:
            raise ValueError('image width cannot be negative integer')
        elif height < 0:
            raise ValueError('image height cannot be negative integer')

        return library.MagickExtentImage(self.wand, width, height, x, y)

    def features(self, distance):
        """Calculate directional image features for each color channel.
        Feature metrics including:

        - angular second moment
        - contrast
        - correlation
        - variance sum of squares
        - inverse difference moment
        - sum average
        - sum varience
        - sum entropy
        - entropy
        - difference variance
        - difference entropy
        - information measures of correlation 1
        - information measures of correlation 2
        - maximum correlation coefficient

        With each metric containing horizontal, vertical, left & right
        diagonal values.

        .. code::

            from wand.image import Image

            with Image(filename='rose:') as img:
                channel_features = img.features(distance=32)
                for channels, features in channel_features.items():
                    print(channels)
                    for feature, directions in features.items():
                        print('  ', feature)
                        for name, value in directions.items():
                            print('    ', name, value)

        :param distance: Define the distance if pixels to calculate.
        :type distance: :class:`numbers.Integral`
        :returns: a dict mapping each color channel with a dict of each
                  feature.
        :rtype: :class:`dict`

        .. versionadded:: 0.5.5
        """
        def build_channel(address, channel):
            feature = ChannelFeature()
            size = ctypes.sizeof(feature)
            ctypes.memmove(ctypes.addressof(feature),
                           feature_ptr + (CHANNELS[channel] * size),
                           size)
            keys = ('horizontal', 'vertical',
                    'left_diagonal', 'right_diagonal')
            feature_dict = {}
            for k in feature._fields_:
                a = k[0]
                feature_dict[a] = dict(zip(keys, getattr(feature, a)))
            return feature_dict
        if MAGICK_VERSION_NUMBER < 0x700:
            method = library.MagickGetImageChannelFeatures
        else:  # pragma: no cover
            method = library.MagickGetImageFeatures
        assertions.assert_unsigned_integer(distance=distance)
        feature_ptr = method(self.wand, distance)
        response = {}
        if feature_ptr:
            colorspace = self.colorspace
            if self.alpha_channel:
                response['alpha'] = build_channel(feature_ptr, 'alpha')
            if colorspace == 'gray':
                response['gray'] = build_channel(feature_ptr, 'gray')
            elif colorspace == 'cmyk':
                response['cyan'] = build_channel(feature_ptr, 'cyan')
                response['magenta'] = build_channel(feature_ptr, 'magenta')
                response['yellow'] = build_channel(feature_ptr, 'yellow')
                response['black'] = build_channel(feature_ptr, 'black')
            else:
                response['red'] = build_channel(feature_ptr, 'red')
                response['green'] = build_channel(feature_ptr, 'green')
                response['blue'] = build_channel(feature_ptr, 'blue')
            feature_ptr = library.MagickRelinquishMemory(feature_ptr)
        return response

    @manipulative
    @trap_exception
    def flip(self):
        """Creates a vertical mirror image by reflecting the pixels around
        the central x-axis.  It manipulates the image in place.

        .. versionadded:: 0.3.0

        """
        return library.MagickFlipImage(self.wand)

    @manipulative
    @trap_exception
    def flop(self):
        """Creates a horizontal mirror image by reflecting the pixels around
        the central y-axis.  It manipulates the image in place.

        .. versionadded:: 0.3.0

        """
        return library.MagickFlopImage(self.wand)

    @trap_exception
    def forward_fourier_transform(self, magnitude=True):
        """Performs a discrete Fourier transform. The image stack is replaced
        with the results. Either a pair of magnitude & phase images, or
        real & imaginary (HDRI).

        .. code::

            from wand.image import Image
            from wand.version import QUANTUM_RANGE

            with Image(filename='source.png') as img:
                img.forward_fourier_transform()
                img.depth = QUANTUM_RANGE
                img.save(filename='fft_%02d.png')

        .. seealso:: :meth:`inverse_fourier_transform` & :meth:`complex`

        .. note::

            ImageMagick must have HDRI support to compute real & imaginary
            components (i.e. ``magnitude=False``).

        :param magnitude: If ``True``, generate magnitude & phase, else
                          real & imaginary. Default ``True``
        :type magnitude: :class:`bool`

        .. versionadded:: 0.5.5
        """
        assertions.assert_bool(magnitude=magnitude)
        return library.MagickForwardFourierTransformImage(self.wand, magnitude)

    @manipulative
    @trap_exception
    def frame(self, matte=None, width=1, height=1, inner_bevel=0,
              outer_bevel=0):
        """Creates a bordered frame around image.
        Inner & outer bevel can simulate a 3D effect.

        :param matte: color of the frame
        :type matte: :class:`wand.color.Color`
        :param width: total size of frame on x-axis
        :type width: :class:`numbers.Integral`
        :param height: total size of frame on y-axis
        :type height: :class:`numbers.Integral`
        :param inner_bevel: inset shadow length
        :type inner_bevel: :class:`numbers.Real`
        :param outer_bevel: outset highlight length
        :type outer_bevel: :class:`numbers.Real`

        .. versionadded:: 0.4.1

        """
        if matte is None:
            matte = Color('gray')
        if isinstance(matte, string_type):
            matte = Color(matte)
        assertions.assert_color(matte=matte)
        assertions.assert_integer(width=width, height=height)
        assertions.assert_real(inner_bevel=inner_bevel,
                               outer_bevel=outer_bevel)
        with matte:
            r = library.MagickFrameImage(self.wand,
                                         matte.resource,
                                         width, height,
                                         inner_bevel, outer_bevel)
        return r

    @manipulative
    @trap_exception
    def function(self, function, arguments, channel=None):
        """Apply an arithmetic, relational, or logical expression to an image.

        Defaults entire image, but can isolate affects to single color channel
        by passing :const:`CHANNELS` value to ``channel`` parameter.

        .. note::

           Support for function methods added in the following versions
           of ImageMagick.

           - ``'polynomial'`` >= 6.4.8-8
           - ``'sinusoid'`` >= 6.4.8-8
           - ``'arcsin'`` >= 6.5.3-1
           - ``'arctan'`` >= 6.5.3-1

        :param function: a string listed in :const:`FUNCTION_TYPES`
        :type function: :class:`basestring`
        :param arguments: a sequence of doubles to apply against ``function``
        :type arguments: :class:`collections.abc.Sequence`
        :param channel: optional :const:`CHANNELS`, defaults all
        :type channel: :class:`basestring`
        :raises ValueError: when a ``function``, or ``channel`` is not
                            defined in there respected constant
        :raises TypeError: if ``arguments`` is not a sequence

        .. versionadded:: 0.4.1
        """
        assertions.string_in_list(FUNCTION_TYPES, 'wand.image.FUNCTION_TYPES',
                                  function=function)
        if not isinstance(arguments, abc.Sequence):
            raise TypeError('expecting sequence of arguments, not ' +
                            repr(arguments))
        argc = len(arguments)
        argv = (ctypes.c_double * argc)(*arguments)
        index = FUNCTION_TYPES.index(function)
        if channel is None:
            r = library.MagickFunctionImage(self.wand, index, argc, argv)
        else:
            ch_channel = self._channel_to_mask(channel)
            # Use channel method if IM6, else create channel mask for IM7.
            if library.MagickFunctionImageChannel:
                r = library.MagickFunctionImageChannel(self.wand,
                                                       ch_channel,
                                                       index,
                                                       argc,
                                                       argv)
            else:  # pragma: no cover
                # Set active channel, and capture mask to restore.
                channel_mask = library.MagickSetImageChannelMask(self.wand,
                                                                 ch_channel)
                r = library.MagickFunctionImage(self.wand, index, argc, argv)
                # Restore original state of channels
                library.MagickSetImageChannelMask(self.wand, channel_mask)
        return r

    @manipulative
    def fx(self, expression, channel=None):
        """Manipulate each pixel of an image by given expression.

        FX will preserver current wand instance, and return a new instance of
        :class:`Image` containing affected pixels.

        Defaults entire image, but can isolate affects to single color channel
        by passing :const:`CHANNELS` value to ``channel`` parameter.

        .. seealso:: The anatomy of FX expressions can be found at
                     http://www.imagemagick.org/script/fx.php


        :param expression: The entire FX expression to apply
        :type expression: :class:`basestring`
        :param channel: Optional channel to target.
        :type channel: :const:`CHANNELS`
        :returns: A new instance of an image with expression applied
        :rtype: :class:`Image`

        .. versionadded:: 0.4.1
        """
        assertions.assert_string(expression=expression)
        c_expression = binary(expression)
        if channel is None:
            new_wand = library.MagickFxImage(self.wand, c_expression)
        else:
            ch_channel = self._channel_to_mask(channel)
            if library.MagickFxImageChannel:
                new_wand = library.MagickFxImageChannel(self.wand,
                                                        ch_channel,
                                                        c_expression)
            else:  # pragma: no cover
                # Set active channel, and capture mask to restore.
                channel_mask = library.MagickSetImageChannelMask(self.wand,
                                                                 ch_channel)
                new_wand = library.MagickFxImage(self.wand, c_expression)
                # Restore original state of channels
                library.MagickSetImageChannelMask(self.wand, channel_mask)
        if new_wand:
            return Image(image=BaseImage(new_wand))
        else:  # pragma: no cover
            self.raise_exception()

    @manipulative
    @trap_exception
    def gamma(self, adjustment_value, channel=None):
        """Gamma correct image.

        Specific color channels can be correct individual. Typical values
        range between 0.8 and 2.3.

        :param adjustment_value: value to adjust gamma level
        :type adjustment_value: :class:`numbers.Real`
        :param channel: optional channel to apply gamma correction
        :type channel: :class:`basestring`
        :raises TypeError: if ``gamma_point`` is not a :class:`numbers.Real`
        :raises ValueError: if ``channel`` is not in :const:`CHANNELS`

        .. versionadded:: 0.4.1

        """
        assertions.assert_real(adjustment_value=adjustment_value)
        if channel is None:
            r = library.MagickGammaImage(self.wand, adjustment_value)
        else:
            ch_const = self._channel_to_mask(channel)
            if library.MagickGammaImageChannel:
                r = library.MagickGammaImageChannel(self.wand,
                                                    ch_const,
                                                    adjustment_value)
            else:  # pragma: no cover
                # Set active channel, and capture mask to restore.
                channel_mask = library.MagickSetImageChannelMask(self.wand,
                                                                 ch_const)
                r = library.MagickGammaImage(self.wand, adjustment_value)
                # Restore original state of channels
                library.MagickSetImageChannelMask(self.wand, channel_mask)
        return r

    @manipulative
    @trap_exception
    def gaussian_blur(self, radius, sigma, channel=None):
        """Blurs the image.  We convolve the image with a gaussian operator
        of the given ``radius`` and standard deviation (``sigma``).
        For reasonable results, the ``radius`` should be larger
        than ``sigma``.  Use a ``radius`` of 0 and :meth:`blur()` selects
        a suitable ``radius`` for you.

        :param radius: the radius of the, in pixels,
                       not counting the center pixel
        :type radius: :class:`numbers.Real`
        :param sigma: the standard deviation of the, in pixels
        :type sigma: :class:`numbers.Real`
        :param channel: Optional color channel to target. See
                        :const:`CHANNELS`
        :type channel: :class:`basestring`

        .. versionadded:: 0.3.3

        .. versionchanged:: 0.5.5
           Added ``channel`` argument.
        """
        assertions.assert_real(radius=radius, sigma=sigma)
        if channel is None:
            r = library.MagickGaussianBlurImage(self.wand, radius, sigma)
        else:
            channel_ch = self._channel_to_mask(channel)
            if MAGICK_VERSION_NUMBER < 0x700:
                r = library.MagickGaussianBlurImageChannel(self.wand,
                                                           channel_ch,
                                                           radius,
                                                           sigma)
            else:  # pragma: no cover
                mask = library.MagickSetImageChannelMask(self.wand, channel_ch)
                r = library.MagickGaussianBlurImage(self.wand, radius, sigma)
                library.MagickSetImageChannelMask(self.wand, mask)
        return r

    @manipulative
    @trap_exception
    def hald_clut(self, image, channel=None):
        """Replace color values by referencing a Higher And Lower Dimension
        (HALD) Color Look Up Table (CLUT). You can generate a HALD image
        by using ImageMagick's `hald:` protocol. ::

            with Image(filename='rose:') as img:
                with Image(filename='hald:3') as hald:
                    hald.gamma(1.367)
                    img.hald_clut(hald)

        :param image: The HALD color matrix.
        :type image: :class:`wand.image.BaseImage`
        :param channel: Optional color channel to target. See
                        :const:`CHANNELS`
        :type channel: :class:`basestring`

        .. versionadded:: 0.5.0

        .. versionchanged:: 0.5.5
           Added ``channel`` argument.
        """
        if not isinstance(image, BaseImage):
            raise TypeError('expecting a base image, not ' + repr(image))
        if channel is None:
            r = library.MagickHaldClutImage(self.wand, image.wand)
        else:
            channel_ch = self._channel_to_mask(channel)
            if MAGICK_VERSION_NUMBER < 0x700:
                r = library.MagickHaldClutImageChannel(self.wand, channel_ch,
                                                       image.wand)
            else:  # pragma: no cover
                mask = library.MagickSetImageChannelMask(self.wand, channel_ch)
                r = library.MagickHaldClutImage(self.wand, image.wand)
                library.MagickSetImageChannelMask(self.wand, mask)
        return r

    @manipulative
    @trap_exception
    def hough_lines(self, width, height=None, threshold=40):
        """Identify lines within an image. Use :meth:`canny` to reduce image
        to a binary edge before calling this method.

        .. warning::

            This class method is only available with ImageMagick 7.0.8-41, or
            greater.

        :param width: Local maxima of neighboring pixels.
        :type width: :class:`numbers.Integral`
        :param height: Local maxima of neighboring pixels.
        :type height: :class:`numbers.Integral`
        :param threshold: Line count to limit. Default to 40.
        :type threshold: :class:`numbers.Integral`
        :raises WandLibraryVersionError: If system's version of ImageMagick
                                         does not support this method.

        .. versionadded:: 0.5.5
        """
        if library.MagickHoughLineImage is None:
            msg = 'Method requires ImageMagick version 7.0.8-41 or greater.'
            raise WandLibraryVersionError(msg)
        if height is None:
            height = width
        assertions.assert_unsigned_integer(width=width, height=height,
                                           threshold=threshold)
        return library.MagickHoughLineImage(self.wand, width, height,
                                            threshold)

    @trap_exception
    def implode(self, amount=0.0, method="undefined"):
        """Creates a "imploding" effect by pulling pixels towards the center
        of the image.

        :param amount: Normalized degree of effect between `0.0` & `1.0`.
        :type amount: :class:`numbers.Real`
        :param method: Which interpolate method to apply to effected pixels.
                       See :const:`PIXEL_INTERPOLATE_METHODS` for a list of
                       options. Only available with ImageMagick-7.
        :type method: :class:`basestring`

        .. versionadded:: 0.5.2
        """
        assertions.assert_real(amount=amount)
        assertions.string_in_list(PIXEL_INTERPOLATE_METHODS,
                                  'wand.image.PIXEL_INTERPOLATE_METHODS',
                                  method=method)
        if MAGICK_VERSION_NUMBER < 0x700:
            r = library.MagickImplodeImage(self.wand, amount)
        else:  # pragma: no cover
            method_idx = PIXEL_INTERPOLATE_METHODS.index(method)
            r = library.MagickImplodeImage(self.wand, amount, method_idx)
        return r

    @trap_exception
    def import_pixels(self, x=0, y=0, width=None, height=None,
                      channel_map='RGB', storage='char', data=None):
        """Import pixel data from a byte-string to
        the image. The instance of :class:`Image` must already
        be allocated with the correct size.

        The ``channel_map`` tells ImageMagick which color
        channels to export, and what order they should be
        written as -- per pixel. Valid entries for
        ``channel_map`` are:

        - ``'R'`` - Red channel
        - ``'G'`` - Green channel
        - ``'B'`` - Blue channel
        - ``'A'`` - Alpha channel (``0`` is transparent)
        - ``'O'`` - Alpha channel (``0`` is opaque)
        - ``'C'`` - Cyan channel
        - ``'Y'`` - Yellow channel
        - ``'M'`` - Magenta channel
        - ``'K'`` - Black channel
        - ``'I'`` - Intensity channel (only for grayscale)
        - ``'P'`` - Padding

        See :const:`STORAGE_TYPES` for a list of valid
        ``storage`` options. This tells ImageMagick
        what type of data it should calculate & write to.
        For example; a storage type of ``'char'`` will write
        a 8-bit value between 0 ~ 255,  a storage type
        of ``'short'`` will write a 16-bit value between
        0 ~ 65535, and a ``'integer'`` will write a
        32-bit value between 0 ~ 4294967295.

        .. note::

            By default, the entire image will be exported
            as ``'char'`` storage with each pixel mapping
            Red, Green, Blue, & Alpha channels.


        :param x: horizontal starting coordinate of raster.
        :type x: :class:`numbers.Integral`
        :param y: vertical starting coordinate of raster.
        :type y: :class:`numbers.Integral`
        :param width: horizontal length of raster.
        :type width: :class:`numbers.Integral`
        :param height: vertical length of raster.
        :type height: :class:`numbers.Integral`
        :param channel_map: a string listing the channel data
                            format for each pixel.
        :type channel_map: :class:`basestring`
        :param storage: what data type each value should
                        be calculated as.
        :type storage: :class:`basestring`

        .. versionadded:: 0.5.0
        """
        _w, _h = self.size
        if width is None:
            width = _w
        if height is None:
            height = _h
        assertions.assert_integer(x=x, y=y, width=width, height=height)
        assertions.string_in_list(STORAGE_TYPES, 'wand.image.STORAGE_TYPES',
                                  storage=storage)
        assertions.assert_string(channel_map=channel_map)
        channel_map = channel_map.upper()
        valid_channels = 'RGBAOCYMKIP'
        for channel in channel_map:
            if channel not in valid_channels:
                raise ValueError('Unknown channel label: ' +
                                 repr(channel))
        if not isinstance(data, abc.Sequence):
            raise TypeError('data must list of values, not' +
                            repr(data))
        # Ensure enough data was given.
        expected_len = width * height * len(channel_map)
        given_len = len(data)
        if expected_len != given_len:
            msg = 'data length should be {0}, not {1}.'.format(
                expected_len,
                given_len
            )
            raise ValueError(msg)
        c_storage_types = [
            None,
            ctypes.c_ubyte,
            ctypes.c_double,
            ctypes.c_float,
            ctypes.c_uint,
            ctypes.c_ulong,
            ctypes.c_double,  # FIXME: Might be c_longdouble ?
            ctypes.c_ushort
        ]
        s_index = STORAGE_TYPES.index(storage)
        c_type = c_storage_types[s_index]
        c_buffer = (len(data) * c_type)(*data)
        r = library.MagickImportImagePixels(self.wand,
                                            x, y, width, height,
                                            binary(channel_map),
                                            s_index,
                                            ctypes.byref(c_buffer))
        return r

    @trap_exception
    def inverse_fourier_transform(self, phase, magnitude=True):
        """Applies the inverse of a discrete Fourier transform. The image stack
        is replaced with the results. Either a pair of magnitude & phase
        images, or real & imaginary (HDRI).

        .. code::

            from wand.image import Image

            with Image(filename='magnitude.png') as img:
                with Image(filename='phase.png') as phase:
                    img.inverse_fourier_transform(phase)
                img.save(filename='output.png')

        .. seealso:: :meth:`forward_fourier_transform` & :meth:`complex`

        .. note::

            ImageMagick must have HDRI support to compute real & imaginary
            components (i.e. ``magnitude=False``).

        :param phase: Second part (image) of the transform. Either the phase,
                      or the imaginary part.
        :type phase: :class:`BaseImage`
        :param magnitude: If ``True``, accept magnitude & phase input, else
                          real & imaginary. Default ``True``
        :type magnitude: :class:`bool`

        .. versionadded:: 0.5.5
        """
        if not isinstance(phase, BaseImage):
            raise TypeError('phase must be an image, not ' + repr(phase))
        assertions.assert_bool(magnitude=magnitude)
        return library.MagickInverseFourierTransformImage(self.wand,
                                                          phase.wand,
                                                          magnitude)

    def kurtosis_channel(self, channel='default_channels'):
        """Calculates the kurtosis and skewness of the image.

        .. code:: python

            from wand.image import Image

            with Image(filename='input.jpg') as img:
                kurtosis, skewness = img.kurtosis_channel()

        :param channel: Select which color channel to evaluate. See
                        :const:`CHANNELS`. Default ``'default_channels'``.
        :type channel: :class:`basestring`
        :returns: Tuple of :attr:`kurtosis` & :attr:`skewness`
                  values.
        :rtype: :class:`tuple`

        .. versionadded:: 0.5.3
        """
        ch_channel = self._channel_to_mask(channel)
        k = ctypes.c_double(0.0)
        s = ctypes.c_double(0.0)
        if MAGICK_VERSION_NUMBER < 0x700:
            library.MagickGetImageChannelKurtosis(self.wand, ch_channel,
                                                  ctypes.byref(k),
                                                  ctypes.byref(s))
        else:  # pragma: no cover
            # Set active channel, and capture mask to restore.
            channel_mask = library.MagickSetImageChannelMask(self.wand,
                                                             ch_channel)
            library.MagickGetImageKurtosis(self.wand,
                                           ctypes.byref(k),
                                           ctypes.byref(s))
            # Restore original state of channels
            library.MagickSetImageChannelMask(self.wand, channel_mask)
        return k.value, s.value

    @manipulative
    @trap_exception
    def kuwahara(self, radius=1.0, sigma=None):
        """Edge preserving noise reduction filter.

        https://en.wikipedia.org/wiki/Kuwahara_filter

        If ``sigma`` is not given, the value will be calculated as:

            sigma = radius - 0.5

        To match original algorithm's behavior, increase ``radius`` value by
        one:

            myImage.kuwahara(myRadius + 1, mySigma)

        .. warning::

            This class method is only available with ImageMagick 7.0.8-41, or
            greater.

        :param radius: Size of the filter aperture.
        :type radius: :class:`numbers.Real`
        :param sigma: Standard deviation of Gaussian filter.
        :type sigma: :class:`numbers.Real`
        :raises WandLibraryVersionError: If system's version of ImageMagick
                                         does not support this method.

        .. versionadded:: 0.5.5
        """
        if library.MagickKuwaharaImage is None:
            msg = 'Method requires ImageMagick version 7.0.8-41 or greater.'
            raise WandLibraryVersionError(msg)
        if sigma is None:
            sigma = radius - 0.5
        assertions.assert_real(radius=radius, sigma=sigma)
        return library.MagickKuwaharaImage(self.wand, radius, sigma)

    @trap_exception
    def level(self, black=0.0, white=None, gamma=1.0, channel=None):
        """Adjusts the levels of an image by scaling the colors falling
        between specified black and white points to the full available
        quantum range.

        If only ``black`` is given, ``white`` will be adjusted inward.

        :param black: Black point, as a percentage of the system's quantum
                      range. Defaults to 0.
        :type black: :class:`numbers.Real`
        :param white: White point, as a percentage of the system's quantum
                      range. Defaults to 1.0.
        :type white: :class:`numbers.Real`
        :param gamma: Optional gamma adjustment. Values > 1.0 lighten the
                      image's midtones while values < 1.0 darken them.
        :type gamma: :class:`numbers.Real`
        :param channel: The channel type. Available values can be found
                        in the :const:`CHANNELS` mapping. If ``None``,
                        normalize all channels.
        :type channel: :const:`CHANNELS`

        .. note::
            Images may not be affected if the ``white`` value is equal, or
            less then, the ``black`` value.

        .. versionadded:: 0.4.1

        """
        assertions.assert_real(black=black)
        # If white is not given, mimic CLI behavior by reducing top point
        if white is None:
            white = 1.0 - black
        assertions.assert_real(white=white, gamma=gamma)

        bp = float(self.quantum_range * black)
        wp = float(self.quantum_range * white)
        if MAGICK_HDRI:
            bp -= 0.5  # TODO: Document why HDRI requires 0.5 adjustments.
            wp -= 0.5
        if channel is None:
            r = library.MagickLevelImage(self.wand, bp, gamma, wp)
        else:
            ch_const = self._channel_to_mask(channel)
            if library.MagickLevelImageChannel:
                r = library.MagickLevelImageChannel(self.wand,
                                                    ch_const,
                                                    bp,
                                                    gamma,
                                                    wp)
            else:  # pragma: no cover
                # Set active channel, and capture mask to restore.
                channel_mask = library.MagickSetImageChannelMask(self.wand,
                                                                 ch_const)
                r = library.MagickLevelImage(self.wand, bp, gamma, wp)
                # Restore original state of channels
                library.MagickSetImageChannelMask(self.wand, channel_mask)
        return r

    @manipulative
    @trap_exception
    def levelize(self, black=0.0, white=None, gamma=1.0, channel=None):
        """Reverse of :meth:`level()`, this method compresses the range of
        colors between ``black`` & ``white`` values.

        If only ``black`` is given, ``white`` will be adjusted inward.

        .. warning::

            This class method is only available with ImageMagick 7.0.8-41, or
            greater.

        :param black: Black point, as a percentage of the system's quantum
                      range. Defaults to 0.
        :type black: :class:`numbers.Real`
        :param white: White point, as a percentage of the system's quantum
                      range. Defaults to 1.0.
        :type white: :class:`numbers.Real`
        :param gamma: Optional gamma adjustment. Values > 1.0 lighten the
                      image's midtones while values < 1.0 darken them.
        :type gamma: :class:`numbers.Real`
        :param channel: The channel type. Available values can be found
                        in the :const:`CHANNELS` mapping. If ``None``,
                        normalize all channels.
        :type channel: :const:`CHANNELS`
        :raises WandLibraryVersionError: If system's version of ImageMagick
                                         does not support this method.

        .. versionadded:: 0.5.5
        """
        if library.MagickLevelizeImage is None:
            msg = 'Method requires ImageMagick version 7.0.8-41 or greater.'
            raise WandLibraryVersionError(msg)
        if white is None:
            white = float(self.quantum_range)
        assertions.assert_real(black=black, white=white, gamma=gamma)
        if 0 < black <= 1.0:
            black *= self.quantum_range
        if 0 < white <= 1.0:
            white *= self.quantum_range
        if channel is None:
            r = library.MagickLevelizeImage(self.wand, black, gamma, white)
        else:
            ch_const = self._channel_to_mask(channel)
            channel_mask = library.MagickSetImageChannelMask(self.wand,
                                                             ch_const)
            r = library.MagickLevelizeImage(self.wand, black, gamma, white)
            library.MagickSetImageChannelMask(self.wand, channel_mask)
        return r

    @manipulative
    @trap_exception
    def linear_stretch(self, black_point=0.0, white_point=1.0):
        """Enhance saturation intensity of an image.

        :param black_point: Black point between 0.0 and 1.0. Default 0.0
        :type black_point: :class:`numbers.Real`
        :param white_point: White point between 0.0 and 1.0. Default 1.0
        :type white_point: :class:`numbers.Real`

        .. versionadded:: 0.4.1
        """
        assertions.assert_real(black_point=black_point,
                               white_point=white_point)
        linear_range = float(self.width * self.height)
        return library.MagickLinearStretchImage(self.wand,
                                                linear_range * black_point,
                                                linear_range * white_point)

    @manipulative
    def liquid_rescale(self, width, height, delta_x=0, rigidity=0):
        """Rescales the image with `seam carving`_, also known as
        image retargeting, content-aware resizing, or liquid rescaling.

        :param width: the width in the scaled image
        :type width: :class:`numbers.Integral`
        :param height: the height in the scaled image
        :type height: :class:`numbers.Integral`
        :param delta_x: maximum seam transversal step.
                        0 means straight seams.  default is 0
        :type delta_x: :class:`numbers.Real`
        :param rigidity: introduce a bias for non-straight seams.
                         default is 0
        :type rigidity: :class:`numbers.Real`
        :raises wand.exceptions.MissingDelegateError:
           when ImageMagick isn't configured ``--with-lqr`` option.

        .. note::

           This feature requires ImageMagick to be configured
           ``--with-lqr`` option.  Or it will raise
           :exc:`~wand.exceptions.MissingDelegateError`:

        .. seealso::

           `Seam carving`_ --- Wikipedia
              The article which explains what seam carving is
              on Wikipedia.

        .. _Seam carving: http://en.wikipedia.org/wiki/Seam_carving

        """
        assertions.assert_integer(width=width, height=height)
        assertions.assert_real(delta_x=delta_x, rigidity=rigidity)
        library.MagickLiquidRescaleImage(self.wand, width, height,
                                         delta_x, rigidity)
        try:
            self.raise_exception()
        except MissingDelegateError as e:
            raise MissingDelegateError(
                str(e) + '\n\nImageMagick in the system is likely to be '
                'impossible to load liblqr.  You might not install liblqr, '
                'or ImageMagick may not compiled with liblqr.'
            )

    @manipulative
    @trap_exception
    def magnify(self):
        """Quickly double an image in size. This is a convenience method.
        Use :meth:`resize()`, :meth:`resample()`, or :meth:`sample()` for
        more control.

        .. versionadded:: 0.5.5
        """
        return library.MagickMagnifyImage(self.wand)

    def mean_channel(self, channel='default_channels'):
        """Calculates the mean and standard deviation of the image.

        .. code:: python

            from wand.image import Image

            with Image(filename='input.jpg') as img:
                mean, stddev = img.mean_channel()

        :param channel: Select which color channel to evaluate. See
                        :const:`CHANNELS`. Default ``'default_channels'``.
        :type channel: :class:`basestring`
        :returns: Tuple of :attr:`mean` & :attr:`standard_deviation`
                  values. The ``mean`` value will be between 0.0 &
                  :attr:`quantum_range`
        :rtype: :class:`tuple`

        .. versionadded:: 0.5.3
        """
        ch_channel = self._channel_to_mask(channel)
        m = ctypes.c_double(0.0)
        s = ctypes.c_double(0.0)
        if MAGICK_VERSION_NUMBER < 0x700:
            library.MagickGetImageChannelMean(self.wand, ch_channel,
                                              ctypes.byref(m),
                                              ctypes.byref(s))
        else:  # pragma: no cover
            # Set active channel, and capture mask to restore.
            channel_mask = library.MagickSetImageChannelMask(self.wand,
                                                             ch_channel)
            library.MagickGetImageMean(self.wand,
                                       ctypes.byref(m),
                                       ctypes.byref(s))
            # Restore original state of channels
            library.MagickSetImageChannelMask(self.wand, channel_mask)
        return m.value, s.value

    @manipulative
    @trap_exception
    def mean_shift(self, width, height, color_distance=0.1):
        """Recalculates pixel value by comparing neighboring pixels within a
        color distance, and replacing with a mean value. Works best with
        Gray, YCbCr, YIQ, or YUV colorspaces.

        .. warning::

            This class method is only available with ImageMagick 7.0.8-41, or
            greater.

        :param width: Size of the neighborhood window in pixels.
        :type width: :class:`numbers.Integral`
        :param height: Size of the neighborhood window in pixels.
        :type height: :class:`numbers.Integral`
        :param color_distance: Include pixel values within this color distance.
        :type color_distance: :class:`numbers.Real`
        :raises WandLibraryVersionError: If system's version of ImageMagick
                                         does not support this method.

        .. versionadded:: 0.5.5
        """
        if library.MagickMeanShiftImage is None:
            msg = 'Method requires ImageMagick version 7.0.8-41 or greater.'
            raise WandLibraryVersionError(msg)
        assertions.assert_counting_number(width=width, height=height)
        assertions.assert_real(color_distance=color_distance)
        if 0 < color_distance <= 1.0:
            color_distance *= self.quantum_range
        return library.MagickMeanShiftImage(self.wand, width, height,
                                            color_distance)

    @manipulative
    def merge_layers(self, method):
        """Composes all the image layers from the current given image onward
        to produce a single image of the merged layers.

        The initial canvas's size depends on the given ImageLayerMethod, and is
        initialized using the first images background color.  The images
        are then composited onto that image in sequence using the given
        composition that has been assigned to each individual image.
        The method must be set with a value from :const:`IMAGE_LAYER_METHOD`
        that is acceptable to this operation. (See ImageMagick documentation
        for more details.)

        :param method: the method of selecting the size of the initial canvas.
        :type method: :class:`basestring`

        .. versionadded:: 0.4.3

        """
        assertions.assert_string(method=method)
        if method not in ('merge', 'flatten', 'mosaic', 'trimbounds'):
            raise ValueError('method can only be \'merge\', \'flatten\', '
                             '\'mosaic\', or \'trimbounds\'')
        m = IMAGE_LAYER_METHOD.index(method)
        r = library.MagickMergeImageLayers(self.wand, m)
        if not r:  # pragma: no cover
            self.raise_exception()
        else:
            self.wand = r

    @manipulative
    def mode(self, width, height=None):
        """Replace each pixel with the mathematical mode of the neighboring
        colors. This is an alias of the :meth:`statistic` method.

        :param width: Number of neighboring pixels to include in mode.
        :type width: :class:`numbers.Integral`
        :param height: Optional height of neighboring pixels, defaults to the
                       same value as ``width``.
        :type height: :class:`numbers.Integral`

        .. versionadded:: 0.5.4
        """
        if height is None:
            height = width
        self.statistic('mode', width, height)

    @manipulative
    @trap_exception
    def modulate(self, brightness=100.0, saturation=100.0, hue=100.0):
        """Changes the brightness, saturation and hue of an image.
        We modulate the image with the given ``brightness``, ``saturation``
        and ``hue``.

        :param brightness: percentage of brightness
        :type brightness: :class:`numbers.Real`
        :param saturation: percentage of saturation
        :type saturation: :class:`numbers.Real`
        :param hue: percentage of hue rotation
        :type hue: :class:`numbers.Real`
        :raises ValueError: when one or more arguments are invalid

        .. versionadded:: 0.3.4

        """
        assertions.assert_real(brightness=brightness, saturation=saturation,
                               hue=hue)
        return library.MagickModulateImage(
            self.wand,
            brightness,
            saturation,
            hue
        )

    @manipulative
    @trap_exception
    def morphology(self, method=None, kernel=None, iterations=1, channel=None):
        """Manipulate pixels based on the shape of neighboring pixels.

        The ``method`` determines what type of effect to apply to matching
        ``kernel`` shapes. Common methods can be add/remove,
        or lighten/darken pixel values.

        The ``kernel`` describes the shape of the matching neighbors. Common
        shapes are provided as "built-in" kernels. See
        :const`KERNEL_INFO_TYPES` for examples. The format for built-in kernels
        is:

        .. sourcecode:: text

            label:geometry

        Where `label` is the kernel name defined in :const:`KERNEL_INFO_TYPES`,
        and `:geometry` is an optional geometry size. For example::

            with Image(filename='rose:') as img:
                img.morphology(method='dilate', kernel='octagon:3x3')
                # or simply
                img.morphology(method='edgein', kernel='octagon')

        Custom kernels can be applied by following a similar format:

        .. sourcecode:: text

            geometry:args

        Where `geometry` is the size of the custom kernel, and `args`
        list a comma separated list of values. For example::

            custom_kernel='5x3:nan,1,1,1,nan 1,1,1,1,1 nan,1,1,1,nan'
            with Image(filename='rose:') as img:
                img.morphology(method='dilate', kernel=custom_kernel)

        :param method: effect function to apply. See
                       :const:`MORPHOLOGY_METHODS` for a list of
                       methods.
        :type method: :class:`basestring`
        :param kernel: shape to evaluate surrounding pixels. See
                       :const:`KERNEL_INFO_TYPES` for a list of
                       built-in shapes.
        :type kernel: :class:`basestring`
        :param iterations: Number of times a morphology method should be
                           applied to the image. Default ``1``. Use ``-1`` for
                           unlimited iterations until the image is unchanged
                           by the method operator.
        :type iterations: :class:`numbers.Integral`
        :param channel: Optional color channel to target. See
                        :const:`CHANNELS`
        :type channel: `basestring`

        .. versionadded:: 0.5.0

        .. versionchanged:: 0.5.5
           Added ``channel`` argument.
        """
        assertions.assert_string(method=method, kernel=kernel)
        assertions.assert_integer(iterations=iterations)
        buitin = None
        geometry = ''
        parts = kernel.split(':')
        if parts[0] in KERNEL_INFO_TYPES:
            buitin = parts[0]
            if len(parts) == 2:
                geometry = parts[1]
        exception_info = libmagick.AcquireExceptionInfo()
        if buitin:
            kernel_idx = KERNEL_INFO_TYPES.index(buitin)
            geometry_info = GeomertyInfo()
            flags = libmagick.ParseGeometry(binary(geometry),
                                            ctypes.byref(geometry_info))
            if buitin in ('unity',):
                if (flags & 0x0004) == 0:
                    geometry_info.rho = 1.0
            elif buitin in ('square', 'diamond', 'octagon', 'disk',
                            'plus', 'cross'):
                if (flags & 0x0008) == 0:
                    geometry_info.sigma = 1.0
            elif buitin in ('ring',):
                if (flags & 0x0001) == 0:
                    geometry_info.xi = 1.0
            elif buitin in ('rectangle',):
                if (flags & 0x0004) == 0:
                    geometry_info.rho = geometry_info.sigma
                if geometry_info.rho < 1.0:
                    geometry_info.rho = 3.0
                if geometry_info.sigma < 1.0:
                    geometry_info.sigma = geometry_info.rho
                if (flags & 0x0001) == 0:
                    geometry_info.xi = (geometry_info.rho - 1.0) / 2.0
                if (flags & 0x0002) == 0:
                    geometry_info.psi = (geometry_info.sigma - 1.0) / 2.0
            elif buitin in ('chebyshev', 'manhattan', 'octagonal',
                            'euclidean'):
                if (flags & 0x0008) == 0:
                    geometry_info.sigma = 100.0
                elif (flags & 0x2000) != 0:
                    geometry_info.sigma = (float(self.quantum_range) /
                                           (geometry_info.sigma + 1.0))
                elif (flags & 0x1000) != 0:
                    geometry_info.sigma *= float(self.quantum_range) / 100.0
            if MAGICK_VERSION_NUMBER < 0x700:
                kernel_info = libmagick.AcquireKernelBuiltIn(
                    kernel_idx,
                    ctypes.byref(geometry_info)
                )
            else:  # pragma: no cover
                kernel_info = libmagick.AcquireKernelBuiltIn(
                    kernel_idx,
                    ctypes.byref(geometry_info),
                    exception_info
                )
        elif kernel:
            if MAGICK_VERSION_NUMBER < 0x700:
                kernel_info = libmagick.AcquireKernelInfo(
                    binary(kernel)
                )
            else:  # pragma: no cover
                kernel_info = libmagick.AcquireKernelInfo(
                    binary(kernel),
                    exception_info
                )
        r = None
        exception_info = libmagick.DestroyExceptionInfo(exception_info)
        if kernel_info:
            method_idx = MORPHOLOGY_METHODS.index(method)
            if channel is None:
                r = library.MagickMorphologyImage(self.wand, method_idx,
                                                  iterations, kernel_info)
            else:
                channel_ch = self._channel_to_mask(channel)
                if MAGICK_VERSION_NUMBER < 0x700:
                    r = library.MagickMorphologyImageChannel(self.wand,
                                                             channel_ch,
                                                             method_idx,
                                                             iterations,
                                                             kernel_info)
                else:  # pragma: no cover
                    mask = library.MagickSetImageChannelMask(self.wand,
                                                             channel_ch)
                    r = library.MagickMorphologyImage(self.wand, method_idx,
                                                      iterations, kernel_info)
                    library.MagickSetImageChannelMask(self.wand, mask)
            kernel_info = libmagick.DestroyKernelInfo(kernel_info)
        else:
            raise ValueError('Unable to parse kernel info for ' +
                             repr(kernel))
        return r

    @manipulative
    @trap_exception
    def motion_blur(self, radius=0.0, sigma=0.0, angle=0.0, channel=None):
        """Apply a Gaussian blur along an ``angle`` direction. This
        simulates motion movement.

        :param radius: Apature size of the Gaussian operator.
        :type radius: :class:`numbers.Real`
        :param sigma: Standard deviation of the Gaussian operator.
        :type sigma: :class:`numbers.Real`
        :param angle: Apply the effect along this angle.
        :type angle: :class:`numbers.Real`

        .. versionadded:: 0.5.4
        """
        assertions.assert_real(radius=radius, sigma=sigma, angle=angle)
        if channel is None:
            r = library.MagickMotionBlurImage(self.wand, radius, sigma, angle)
        else:
            ch_const = self._channel_to_mask(channel)
            if MAGICK_VERSION_NUMBER < 0x700:
                r = library.MagickMotionBlurImageChannel(self.wand,
                                                         ch_const,
                                                         radius,
                                                         sigma,
                                                         angle)
            else:  # pragma: no cover
                # Set active channel, and capture mask to restore.
                channel_mask = library.MagickSetImageChannelMask(self.wand,
                                                                 ch_const)
                r = library.MagickMotionBlurImage(self.wand, radius, sigma,
                                                  angle)
                # Restore original state of channels
                library.MagickSetImageChannelMask(self.wand, channel_mask)
        return r

    @trap_exception
    def negate(self, grayscale=False, channel=None):
        """Negate the colors in the reference image.

        :param grayscale: if set, only negate grayscale pixels in the image.
        :type grayscale: :class:`bool`
        :param channel: the channel type.  available values can be found
                        in the :const:`CHANNELS` mapping.  If ``None``,
                        negate all channels.
        :type channel: :class:`basestring`

        .. versionadded:: 0.3.8

        """
        if channel is None:
            r = library.MagickNegateImage(self.wand, grayscale)
        else:
            ch_const = self._channel_to_mask(channel)
            if library.MagickNegateImageChannel:
                r = library.MagickNegateImageChannel(self.wand, ch_const,
                                                     grayscale)
            else:  # pragma: no cover
                # Set active channel, and capture mask to restore.
                channel_mask = library.MagickSetImageChannelMask(self.wand,
                                                                 ch_const)
                r = library.MagickNegateImage(self.wand, grayscale)
                # Restore original state of channels
                library.MagickSetImageChannelMask(self.wand, channel_mask)
        return r

    @manipulative
    @trap_exception
    def noise(self, noise_type='uniform', attenuate=1.0, channel=None):
        """Adds noise to image.

        :param noise_type: type of noise to apply. See :const:`NOISE_TYPES`.
        :type noise_type: :class:`basestring`
        :param attenuate: rate of distribution. Only available in
                          ImageMagick-7. Default is ``1.0``.
        :type attenuate: :class:`numbers.Real`
        :param channel: Optionally target a color channel to apply noise to.
                        See :const:`CHANNELS`.
        :type channel: :class:`basestring`

        .. versionadded:: 0.5.3

        .. versionchanged:: 0.5.5
           Added optional ``channel`` argument.
        """
        assertions.string_in_list(NOISE_TYPES, 'wand.image.NOISE_TYPES',
                                  noise_type=noise_type)
        assertions.assert_real(attenuate=attenuate)
        noise_type_idx = NOISE_TYPES.index(noise_type)
        if MAGICK_VERSION_NUMBER < 0x700:
            if channel is None:
                r = library.MagickAddNoiseImage(self.wand, noise_type_idx)
            else:
                channel_ch = self._channel_to_mask(channel)
                r = library.MagickAddNoiseImageChannel(self.wand,
                                                       channel_ch,
                                                       noise_type_idx)
        else:  # pragma: no cover
            if channel is None:
                r = library.MagickAddNoiseImage(self.wand, noise_type_idx,
                                                attenuate)
            else:
                channel_ch = self._channel_to_mask(channel)
                mask = library.MagickSetImageChannelMask(self.wand,
                                                         channel_ch)
                r = library.MagickAddNoiseImage(self.wand, noise_type_idx,
                                                attenuate)
                library.MagickSetImageChannelMask(self.wand, mask)
        return r

    @manipulative
    @trap_exception
    def normalize(self, channel=None):
        """Normalize color channels.

        :param channel: the channel type.  available values can be found
                        in the :const:`CHANNELS` mapping.  If ``None``,
                        normalize all channels.
        :type channel: :class:`basestring`

        """
        if channel is None:
            r = library.MagickNormalizeImage(self.wand)
        else:
            ch_const = self._channel_to_mask(channel)
            if library.MagickNormalizeImageChannel:
                r = library.MagickNormalizeImageChannel(self.wand, ch_const)
            else:  # pragma: no cover
                with Image(image=self) as mask:
                    # Set active channel, and capture mask to restore.
                    channel_mask = library.MagickSetImageChannelMask(mask.wand,
                                                                     ch_const)
                    r = library.MagickNormalizeImage(mask.wand)
                    # Restore original state of channels.
                    library.MagickSetImageChannelMask(mask.wand,
                                                      channel_mask)
                    # Copy adjusted mask over original value.
                    copy_mask = COMPOSITE_OPERATORS.index('copy_' + channel)
                    library.MagickCompositeImage(self.wand,
                                                 mask.wand,
                                                 copy_mask,
                                                 False,
                                                 0,
                                                 0)
        return r

    @manipulative
    @trap_exception
    def oil_paint(self, radius=0.0, sigma=0.0):
        """Simulates an oil painting by replace each pixel with most frequent
        surrounding color.

        :param radius: The size of the surrounding neighbors.
        :type radius: :class:`numbers.Real`
        :param sigma: The standard deviation used by the Gaussian operator.
                      This is only available with ImageMagick-7.
        :type sigma: :class:`numbers.Real`

        .. versionadded:: 0.5.4
        """
        assertions.assert_real(radius=radius, sigma=sigma)
        if MAGICK_VERSION_NUMBER < 0x700:
            r = library.MagickOilPaintImage(self.wand, radius)
        else:
            r = library.MagickOilPaintImage(self.wand, radius, sigma)
        return r

    @manipulative
    @trap_exception
    def opaque_paint(self, target=None, fill=None, fuzz=0.0, invert=False,
                     channel=None):
        """Replace any color that matches ``target`` with ``fill``. Use
        ``fuzz`` to control the threshold of the target match.
        The ``invert`` will replace all colors *but* the  pixels matching
        the ``target`` color.

        :param target: The color to match.
        :type target: :class:`wand.color.Color`
        :param fill: The color to paint with.
        :type fill: :class:`wand.color.Color`
        :param fuzz: Normalized real number between `0.0` and
                     :attr:`quantum_range`. Default is `0.0`.
        :type fuzz: class:`numbers.Real`
        :param invert: Replace all colors that do not match target.
                       Default is ``False``.
        :type invert: :class:`bool`
        :param channel: Optional color channel to target. See
                        :const:`CHANNELS`
        :type channel: :class:`basestring`

        .. versionadded:: 0.5.4

        .. versionchanged:: 0.5.5
           Added ``channel`` paramater.
        """
        if isinstance(target, string_type):
            target = Color(target)
        if isinstance(fill, string_type):
            fill = Color(fill)
        assertions.assert_color(target=target, fill=fill)
        assertions.assert_real(fuzz=fuzz)
        assertions.assert_bool(invert=invert)
        with target:
            with fill:
                if channel is None:
                    r = library.MagickOpaquePaintImage(self.wand,
                                                       target.resource,
                                                       fill.resource,
                                                       fuzz,
                                                       invert)
                else:
                    channel_ch = self._channel_to_mask(channel)
                    if MAGICK_VERSION_NUMBER < 0x700:
                        r = library.MagickOpaquePaintImageChannel(
                            self.wand, channel_ch, target.resource,
                            fill.resource, fuzz, invert
                        )
                    else:  # pragma: no cover
                        mask = library.MagickSetImageChannelMask(self.wand,
                                                                 channel_ch)
                        r = library.MagickOpaquePaintImage(self.wand,
                                                           target.resource,
                                                           fill.resource,
                                                           fuzz,
                                                           invert)
                        library.MagickSetImageChannelMask(self.wand, mask)
        return r

    @manipulative
    def optimize_layers(self):
        """Attempts to crop each frame to the smallest image without altering
        the animation.

        .. note::

            This will only affect ``GIF`` image formates.

        .. versionadded:: 0.5.0
        """
        r = library.MagickOptimizeImageLayers(self.wand)
        if not r:  # pragma: no cover
            self.raise_exception()
        self.wand = r

    @manipulative
    @trap_exception
    def optimize_transparency(self):
        """Iterates over frames, and sets transparent values for each
        pixel unchanged by previous frame.

        .. note::

            This will only affect ``GIF`` image formates.

        .. versionadded:: 0.5.0
        """
        if library.MagickOptimizeImageTransparency:
            return library.MagickOptimizeImageTransparency(self.wand)
        else:  # pragma: no cover
            raise AttributeError('`MagickOptimizeImageTransparency\' not '
                                 'available on current version of MagickWand '
                                 'library.')

    def percent_escape(self, string_format):
        """Convenience method that expands ImageMagick's `Percent Escape`_
        characters into image attribute values.

        .. _Percent Escape: https://imagemagick.org/script/escape.php

        .. code::

            with wand.image import Image

            with Image(filename='tests/assets/sasha.jpg ') as img:
                print(img.percent_escape('%f %wx%h'))
                #=> sasha.jpg 204x247

        .. note::

            Not all percent escaped values can be populated as I/O operations
            are managed by Python, and not the CLI utility.

        :param string_format: The precent escaped string to be translated.
        :type string_format: :class:`basestring`
        :returns: String of expanded values.
        :rtype: :class:`basestring`

        .. versionadded:: 0.5.6
        """
        local_overwrites = {
            '%m': self.format,
            '%[magick]': self.format
        }
        for k, v in local_overwrites.items():
            string_format = string_format.replace(k, v)
        self.options['format'] = string_format
        return text(self.make_blob('INFO'))

    @manipulative
    @trap_exception
    def polaroid(self, angle=0.0, caption=None, font=None, method='undefined'):
        """Creates a special effect simulating a Polaroid photo.

        :param angle: applies a shadow effect along this angle.
        :type angle: :class:`numbers.Real`
        :param caption: Writes a message at the bottom of the photo's border.
        :type caption: :class:`basestring`
        :param font: Specify font style.
        :type font: :class:`wand.font.Font`
        :param method: Interpolation method. ImageMagick-7 only.
        :type method: :class:`basestring`

        .. versionadded:: 0.5.4
        """
        assertions.assert_real(angle=angle)
        assertions.string_in_list(PIXEL_INTERPOLATE_METHODS,
                                  'wand.image.PIXEL_INTERPOLATE_METHODS',
                                  method=method)
        ctx_ptr = library.NewDrawingWand()
        if caption:
            assertions.assert_string(caption=caption)
            caption = binary(caption)
            library.MagickSetImageProperty(self.wand, b'Caption',
                                           caption)
            if isinstance(font, Font):
                if font.path:
                    library.DrawSetFont(ctx_ptr, binary(font.path))
                if font.size:
                    library.DrawSetFontSize(ctx_ptr, font.size)
                if font.color:
                    with font.color:
                        library.DrawSetFillColor(ctx_ptr, font.color.resource)
                library.DrawSetTextAntialias(ctx_ptr, font.antialias)
                if font.stroke_color:
                    with font.stroke_color:
                        library.DrawSetStrokeColor(ctx_ptr,
                                                   font.stroke_color.resource)
                if font.stroke_width:
                    library.DrawSetStrokeWidth(ctx_ptr, font.stroke_width)
            elif font:
                raise TypeError('font must be in instance of '
                                'wand.font.Font, not ' + repr(font))
        if MAGICK_VERSION_NUMBER < 0x700:
            r = library.MagickPolaroidImage(self.wand, ctx_ptr, angle)
        else:  # pragma: no cover
            method_idx = PIXEL_INTERPOLATE_METHODS.index(method)
            r = library.MagickPolaroidImage(self.wand, ctx_ptr, caption, angle,
                                            method_idx)
        ctx_ptr = library.DestroyDrawingWand(ctx_ptr)
        return r

    @manipulative
    @trap_exception
    def polynomial(self, arguments):
        """Replace image with the sum of all images in a sequence by
        calculating the pixel values a coefficient-weight value, and a
        polynomial-exponent.

        For example::

            with Image(filename='rose:') as img:
                img.polynomial(arguments=[0.5, 1.0])

        The output image will be calculated as:

            output = 0.5 * image ^ 1.0

        .. warning::

            This class method is only available with ImageMagick 7.0.8-41, or
            greater.

        :param arguments: A list of real numbers where at least two numbers
                         (weight & exponent) are need for each image in the
                         sequence.
        :type arguments: :class:`collections.abc.Sequence`
        :raises WandLibraryVersionError: If system's version of ImageMagick
                                         does not support this method.

        .. versionadded:: 0.5.5
        """
        if library.MagickPolynomialImage is None:
            msg = 'Method requires ImageMagick version 7.0.8-41 or greater.'
            raise WandLibraryVersionError(msg)
        if not isinstance(arguments, abc.Sequence):
            raise TypeError('expected sequence of doubles, not ' +
                            repr(arguments))
        argc = len(arguments)
        argv = (ctypes.c_double * argc)(*arguments)
        return library.MagickPolynomialImage(self.wand, (argc >> 1), argv)

    @manipulative
    @trap_exception
    def posterize(self, levels=None, dither='no'):
        """Reduce color levels per channel.

        :param levels: Number of levels per channel.
        :type levels: :class:`numbers.Integral`
        :param dither: Dither method to apply.
                       See :const:`DITHER_METHODS`.
        :type dither: `basestring`

        .. versionadded:: 0.5.0
        """
        assertions.assert_integer(levels=levels)
        assertions.string_in_list(DITHER_METHODS, 'wand.image.DITHER_METHODS',
                                  dither=dither)
        dither_idx = DITHER_METHODS.index(dither)
        return library.MagickPosterizeImage(self.wand, levels, dither_idx)

    @manipulative
    @trap_exception
    def quantize(self, number_colors, colorspace_type,
                 treedepth, dither, measure_error):
        """`quantize` analyzes the colors within a sequence of images and
        chooses a fixed number of colors to represent the image. The goal of
        the algorithm is to minimize the color difference between the input and
        output image while minimizing the processing time.

        :param number_colors: the number of colors.
        :type number_colors: :class:`numbers.Integral`
        :param colorspace_type: colorspace_type. available value can be found
                                in the :const:`COLORSPACE_TYPES`
        :type colorspace_type: :class:`basestring`
        :param treedepth: normally, this integer value is zero or one.
                          a zero or one tells :meth:`quantize` to choose
                          a optimal tree depth of ``log4(number_colors)``.
                          a tree of this depth generally allows the best
                          representation of the reference image
                          with the least amount of memory and
                          the fastest computational speed.
                          in some cases, such as an image with low color
                          dispersion (a few number of colors), a value other
                          than ``log4(number_colors)`` is required.
                          to expand the color tree completely,
                          use a value of 8
        :type treedepth: :class:`numbers.Integral`
        :param dither: a value other than zero distributes the difference
                       between an original image and the corresponding
                       color reduced algorithm to neighboring pixels along
                       a Hilbert curve
        :type dither: :class:`bool`
        :param measure_error: a value other than zero measures the difference
                              between the original and quantized images.
                              this difference is the total quantization error.
                              The error is computed by summing over all pixels
                              in an image the distance squared in RGB space
                              between each reference pixel value and
                              its quantized value
        :type measure_error: :class:`bool`

        .. versionadded:: 0.4.2

        """
        assertions.assert_integer(number_colors=number_colors)
        assertions.string_in_list(COLORSPACE_TYPES,
                                  'wand.image.COLORSPACE_TYPES',
                                  colorspace_type=colorspace_type)
        assertions.assert_integer(treedepth=treedepth)
        assertions.assert_bool(dither=dither, measure_error=measure_error)
        return library.MagickQuantizeImage(
            self.wand, number_colors,
            COLORSPACE_TYPES.index(colorspace_type),
            treedepth, dither, measure_error
        )

    def range_channel(self, channel='default_channels'):
        """Calculate the minimum and maximum of quantum values in image.

        .. code:: python

            from wand.image import Image

            with Image(filename='input.jpg') as img:
                minima, maxima = img.range_channel()

        :param channel: Select which color channel to evaluate. See
                        :const:`CHANNELS`. Default ``'default_channels'``.
        :type channel: :class:`basestring`
        :returns: Tuple of :attr:`minima` & :attr:`maxima`
                  values. Each value will be between 0.0 &
                  :attr:`quantum_range`.
        :rtype: :class:`tuple`

        .. versionadded:: 0.5.3
        """
        ch_channel = self._channel_to_mask(channel)
        min_color = ctypes.c_double(0.0)
        max_color = ctypes.c_double(0.0)
        if MAGICK_VERSION_NUMBER < 0x700:
            library.MagickGetImageChannelRange(self.wand, ch_channel,
                                               ctypes.byref(min_color),
                                               ctypes.byref(max_color))
        else:  # pragma: no cover
            # Set active channel, and capture mask to restore.
            channel_mask = library.MagickSetImageChannelMask(self.wand,
                                                             ch_channel)
            library.MagickGetImageRange(self.wand,
                                        ctypes.byref(min_color),
                                        ctypes.byref(max_color))
            # Restore original state of channels
            library.MagickSetImageChannelMask(self.wand, channel_mask)
        return min_color.value, max_color.value

    @manipulative
    @trap_exception
    def range_threshold(self, low_black=0.0, low_white=None, high_white=None,
                        high_black=None):
        """Applies soft & hard thresholding.

        For a soft thresholding, parameters should be monotonically increasing:

            with Image(filename='text.png') as img:
                img.range_threshold(0.2, 0.4, 0.6, 0.8)

        For a hard thresholding, parameters should be the same:

            with Image(filename='text.png') as img:
                img.range_threshold(0.4, 0.4, 0.6, 0.6)

        .. warning::

            This class method is only available with ImageMagick 7.0.8-41, or
            greater.

        :param low_black: Define the minimum threshold value.
        :type low_black: :class:`numbers.Real`
        :param low_white: Define the minimum threshold value.
        :type low_white: :class:`numbers.Real`
        :param high_white: Define the maximum threshold value.
        :type high_white: :class:`numbers.Real`
        :param high_black: Define the maximum threshold value.
        :type high_black: :class:`numbers.Real`
        :raises WandLibraryVersionError: If system's version of ImageMagick
                                         does not support this method.

        .. versionadded:: 0.5.5
        """
        if library.MagickRangeThresholdImage is None:
            msg = 'Method requires ImageMagick version 7.0.8-41 or greater.'
            raise WandLibraryVersionError(msg)
        # Populate defaults to follow CLI behavior
        if low_white is None:
            low_white = low_black
        if high_white is None:
            high_white = low_white
        if high_black is None:
            high_black = high_white
        assertions.assert_real(low_black=low_black, low_white=low_white,
                               high_white=high_white, high_black=high_black)
        if 0 < low_black <= 1.0:
            low_black *= self.quantum_range
        if 0 < low_white <= 1.0:
            low_white *= self.quantum_range
        if 0 < high_white <= 1.0:
            high_white *= self.quantum_range
        if 0 < high_black <= 1.0:
            high_black *= self.quantum_range
        return library.MagickRangeThresholdImage(self.wand,
                                                 low_black, low_white,
                                                 high_white, high_black)

    @manipulative
    @trap_exception
    def remap(self, affinity=None, method='no'):
        """Rebuild image palette with closest color from given affinity image.

        :param affinity: reference image.
        :type affinity: :class:`BaseImage`
        :param method: dither method. See :const:`DITHER_METHODS`.
                       Default is ``'no'`` dither.
        :type method: :class:`basestring`

        .. versionadded:: 0.5.3
        """
        if not isinstance(affinity, BaseImage):
            raise TypeError('Expecting affinity to be a BaseImage, not ' +
                            repr(affinity))
        assertions.string_in_list(DITHER_METHODS, 'wand.image.DITHER_METHODS',
                                  method=method)
        method_idx = DITHER_METHODS.index(method)
        return library.MagickRemapImage(self.wand, affinity.wand, method_idx)

    @manipulative
    def resample(self, x_res=None, y_res=None, filter='undefined', blur=1):
        """Adjust the number of pixels in an image so that when displayed at
        the given Resolution or Density the image will still look the same size
        in real world terms.

        :param x_res: the X resolution (density) in the scaled image. default
                      is  the original resolution.
        :type x_res: :class:`numbers.Real`
        :param y_res: the Y resolution (density) in the scaled image. default
                      is the original resolution.
        :type y_res: :class:`numbers.Real`
        :param filter: a filter type to use for resizing. choose one in
                       :const:`FILTER_TYPES`. default is ``'undefined'``
                       which means IM will try to guess best one to use.
        :type filter: :class:`basestring`, :class:`numbers.Integral`
        :param blur: the blur factor where > 1 is blurry, < 1 is sharp.
                     default is 1
        :type blur: :class:`numbers.Real`

        .. versionadded:: 0.4.5
        """
        if x_res is None:
            x_res, _ = self.resolution
        if y_res is None:
            _, y_res = self.resolution
        assertions.assert_real(x_res=x_res, y_res=y_res, blur=blur)
        if x_res < 1:
            raise ValueError('x_res must be a Real number, not ' +
                             repr(x_res))
        elif y_res < 1:
            raise ValueError('y_res must be a Real number, not ' +
                             repr(y_res))
        elif not isinstance(filter, (string_type, numbers.Integral)):
            raise TypeError('filter must be one string defined in wand.image.'
                            'FILTER_TYPES or an integer, not ' + repr(filter))
        if isinstance(filter, string_type):
            try:
                filter = FILTER_TYPES.index(filter)
            except IndexError:
                raise ValueError(repr(filter) + ' is an invalid filter type; '
                                 'choose on in ' + repr(FILTER_TYPES))
        elif (isinstance(filter, numbers.Integral) and
              not (0 <= filter < len(FILTER_TYPES))):
            raise ValueError(repr(filter) + ' is an invalid filter type')
        blur = ctypes.c_double(float(blur))
        if self.animation:
            self.wand = library.MagickCoalesceImages(self.wand)
            library.MagickSetLastIterator(self.wand)
            n = library.MagickGetIteratorIndex(self.wand)
            library.MagickResetIterator(self.wand)
            for i in xrange(n + 1):
                library.MagickSetIteratorIndex(self.wand, i)
                library.MagickResampleImage(self.wand, x_res, y_res,
                                            filter, blur)
        else:
            r = library.MagickResampleImage(self.wand, x_res, y_res,
                                            filter, blur)

            if not r:
                self.raise_exception()

    def reset_coords(self):
        """Reset the coordinate frame of the image so to the upper-left corner
        is (0, 0) again (crop and rotate operations change it).

        .. versionadded:: 0.2.0

        """
        library.MagickResetImagePage(self.wand, None)

    @manipulative
    def resize(self, width=None, height=None, filter='undefined', blur=1):
        """Resizes the image.

        :param width: the width in the scaled image. default is the original
                      width
        :type width: :class:`numbers.Integral`
        :param height: the height in the scaled image. default is the original
                       height
        :type height: :class:`numbers.Integral`
        :param filter: a filter type to use for resizing. choose one in
                       :const:`FILTER_TYPES`. default is ``'undefined'``
                       which means IM will try to guess best one to use
        :type filter: :class:`basestring`, :class:`numbers.Integral`
        :param blur: the blur factor where > 1 is blurry, < 1 is sharp.
                     default is 1
        :type blur: :class:`numbers.Real`

        .. versionchanged:: 0.2.1
           The default value of ``filter`` has changed from ``'triangle'``
           to ``'undefined'`` instead.

        .. versionchanged:: 0.1.8
           The ``blur`` parameter changed to take :class:`numbers.Real`
           instead of :class:`numbers.Rational`.

        .. versionadded:: 0.1.1

        """
        if width is None:
            width = self.width
        if height is None:
            height = self.height
        assertions.assert_counting_number(width=width, height=height)
        assertions.assert_real(blur=blur)
        if not isinstance(filter, (string_type, numbers.Integral)):
            raise TypeError('filter must be one string defined in wand.image.'
                            'FILTER_TYPES or an integer, not ' + repr(filter))
        if isinstance(filter, string_type):
            try:
                filter = FILTER_TYPES.index(filter)
            except IndexError:
                raise ValueError(repr(filter) + ' is an invalid filter type; '
                                 'choose on in ' + repr(FILTER_TYPES))
        elif (isinstance(filter, numbers.Integral) and
              not (0 <= filter < len(FILTER_TYPES))):
            raise ValueError(repr(filter) + ' is an invalid filter type')
        blur = ctypes.c_double(float(blur))
        if self.animation:
            self.wand = library.MagickCoalesceImages(self.wand)
            library.MagickSetLastIterator(self.wand)
            n = library.MagickGetIteratorIndex(self.wand)
            library.MagickResetIterator(self.wand)
            for i in xrange(n + 1):
                library.MagickSetIteratorIndex(self.wand, i)
                library.MagickResizeImage(self.wand, width, height,
                                          filter, blur)
            library.MagickSetSize(self.wand, width, height)
        else:
            r = library.MagickResizeImage(self.wand, width, height,
                                          filter, blur)
            library.MagickSetSize(self.wand, width, height)
            if not r:  # pragma: no cover
                self.raise_exception()

    @manipulative
    def rotate(self, degree, background=None, reset_coords=True):
        """Rotates the image right.  It takes a ``background`` color
        for ``degree`` that isn't a multiple of 90.

        :param degree: a degree to rotate. multiples of 360 affect nothing
        :type degree: :class:`numbers.Real`
        :param background: an optional background color.
                           default is transparent
        :type background: :class:`wand.color.Color`
        :param reset_coords: optional flag. If set, after the rotation, the
            coordinate frame will be relocated to the upper-left corner of
            the new image. By default is `True`.
        :type reset_coords: :class:`bool`

        .. versionadded:: 0.2.0
           The ``reset_coords`` parameter.

        .. versionadded:: 0.1.8

        """
        if background is None:
            background = Color('transparent')
        elif isinstance(background, string_type):
            background = Color(background)
        assertions.assert_color(background=background)
        assertions.assert_real(degree=degree)
        with background:
            if self.animation:
                self.wand = library.MagickCoalesceImages(self.wand)
                library.MagickSetLastIterator(self.wand)
                n = library.MagickGetIteratorIndex(self.wand)
                library.MagickResetIterator(self.wand)
                for i in range(0, n + 1):
                    library.MagickSetIteratorIndex(self.wand, i)
                    library.MagickRotateImage(self.wand,
                                              background.resource,
                                              degree)
                    if reset_coords:
                        library.MagickResetImagePage(self.wand, None)
            else:
                result = library.MagickRotateImage(self.wand,
                                                   background.resource,
                                                   degree)
                if not result:  # pragma: no cover
                    self.raise_exception()
                if reset_coords:
                    self.reset_coords()

    @manipulative
    @trap_exception
    def rotational_blur(self, angle=0.0, channel=None):
        """Blur an image in a radius around the center of an image.

        .. warning:: Requires ImageMagick-6.8.8 or greater.

        :param angle: Degrees of rotation to blur with.
        :type angle: :class:`numbers.Real`
        :param channel: Optional channel to apply the effect against. See
                        :const:`CHANNELS` for a list of possible values.
        :type channel: :class:`basestring`
        :raises WandLibraryVersionError: If system's version of ImageMagick
                                         does not support this method.

        .. versionadded:: 0.5.4
        """
        if not library.MagickRotationalBlurImage:
            msg = ("Method `rotational_blur` not available on installed "
                   "version of ImageMagick library. ")
            raise WandLibraryVersionError(msg)
        assertions.assert_real(angle=angle)
        if channel:
            channel_ch = self._channel_to_mask(channel)
            if MAGICK_VERSION_NUMBER < 0x700:
                r = library.MagickRotationalBlurImageChannel(self.wand,
                                                             channel_ch,
                                                             angle)
            else:  # pragma: no cover
                channel_mask = library.MagickSetImageChannelMask(self.wand,
                                                                 channel_ch)
                r = library.MagickRotationalBlurImage(self.wand, angle)
                library.MagickSetImageChannelMask(self.wand, channel_mask)
        else:
            r = library.MagickRotationalBlurImage(self.wand, angle)
        return r

    @manipulative
    def sample(self, width=None, height=None):
        """Resizes the image by sampling the pixels.  It's basically quicker
        than :meth:`resize()` except less quality as a tradeoff.

        :param width: the width in the scaled image. default is the original
                      width
        :type width: :class:`numbers.Integral`
        :param height: the height in the scaled image. default is the original
                       height
        :type height: :class:`numbers.Integral`

        .. versionadded:: 0.3.4

        """
        if width is None:
            width = self.width
        if height is None:
            height = self.height
        assertions.assert_counting_number(width=width, height=height)
        if self.animation:
            self.wand = library.MagickCoalesceImages(self.wand)
            library.MagickSetLastIterator(self.wand)
            n = library.MagickGetIteratorIndex(self.wand)
            library.MagickResetIterator(self.wand)
            for i in xrange(n + 1):
                library.MagickSetIteratorIndex(self.wand, i)
                library.MagickSampleImage(self.wand, width, height)
            library.MagickSetSize(self.wand, width, height)
        else:
            r = library.MagickSampleImage(self.wand, width, height)
            library.MagickSetSize(self.wand, width, height)
            if not r:  # pragma: no cover
                self.raise_exception()

    @manipulative
    @trap_exception
    def selective_blur(self, radius, sigma, threshold, channel=None):
        """Blur an image within a given threshold.

        For best effects, use a value between 10% and 50% of
        :attr:`quantum_range`

        .. code::

            from wand.image import Image

            with Image(filename='photo.jpg') as img:
                # Apply 8x3 blur with a 10% threshold
                img.selective_blur(8.0, 3.0, 0.1 * img.quantum_range)

        :param radius: Size of gaussian apature.
        :type radius: :class:`numbers.Real`
        :param sigma: Standard deviation of gaussian operator.
        :type sigma: :class:`numbers.Real`
        :param threshold: Only pixels within contrast threshold are effected.
                          Value should be between ``0.0`` and
                          :attr:`quantum_range`.
        :type threshold: :class:`numbers.Real`
        :param channel: Optional color channel to target. See
                        :const:`CHANNELS`
        :type channel: :class:`basestring`

        .. versionadded:: 0.5.3

        .. versionchanged:: 0.5.5
           Added ``channel`` argument.
        """
        assertions.assert_real(radius=radius, sigma=sigma, threshold=threshold)
        if channel is None:
            r = library.MagickSelectiveBlurImage(self.wand,
                                                 radius,
                                                 sigma,
                                                 threshold)
        else:
            channel_ch = self._channel_to_mask(channel)
            if MAGICK_VERSION_NUMBER < 0x700:
                r = library.MagickSelectiveBlurImageChannel(self.wand,
                                                            channel_ch,
                                                            radius,
                                                            sigma,
                                                            threshold)
            else:  # pragma: no cover
                mask = library.MagickSetImageChannelMask(self.wand, channel_ch)
                r = library.MagickSelectiveBlurImage(self.wand,
                                                     radius,
                                                     sigma,
                                                     threshold)
                library.MagickSetImageChannelMask(self.wand, mask)
        return r

    @manipulative
    @trap_exception
    def shade(self, gray=False, azimuth=0.0, elevation=0.0):
        """Creates a 3D effect by simulating a light from an
        elevated angle.

        :param gray: Isolate the effect on pixel intensity.
                     Default is False.
        :type gray: :class:`bool`
        :param azimuth: Angle from x-axis.
        :type azimuth: :class:`numbers.Real`
        :param elevation: Amount of pixels from the z-axis.
        :type elevation: :class:`numbers.Real`

        .. versionadded:: 0.5.0
        """
        assertions.assert_real(azimuth=azimuth, elevation=elevation)
        return library.MagickShadeImage(self.wand, gray,
                                        azimuth, elevation)

    @manipulative
    @trap_exception
    def shadow(self, alpha=0.0, sigma=0.0, x=0, y=0):
        """Generates an image shadow.

        :param alpha: Ratio of transparency.
        :type alpha: :class:`numbers.Real`
        :param sigma: Standard deviation of the gaussian filter.
        :type sigma: :class:`numbers.Real`
        :param x: x-offset.
        :type x: :class:`numbers.Integral`
        :param y: y-offset.
        :type y: :class:`numbers.Integral`

        .. versionadded:: 0.5.0
        """
        assertions.assert_real(alpha=alpha, sigma=sigma)
        assertions.assert_integer(x=x, y=y)
        return library.MagickShadowImage(self.wand, alpha, sigma, x, y)

    @manipulative
    @trap_exception
    def sharpen(self, radius=0.0, sigma=0.0, channel=None):
        """Applies a gaussian effect to enhance the sharpness of an
        image.

        .. note::

            For best results, ensure ``radius`` is larger than
            ``sigma``.

            Defaults values of zero will have ImageMagick attempt
            to auto-select suitable values.

        :param radius: size of gaussian aperture.
        :type radius: :class:`numbers.Real`
        :param sigma: Standard deviation of the gaussian filter.
        :type sigma: :class:`numbers.Real`
        :param channel: Optional color channel to target. See
                        :const:`CHANNELS`.
        :type channel: :class:`basestring`

        .. versionadded:: 0.5.0

        .. versionchanged:: 0.5.5
           Added ``channel`` argument.
        """
        assertions.assert_real(radius=radius, sigma=sigma)
        if channel is None:
            r = library.MagickSharpenImage(self.wand, radius, sigma)
        else:
            channel_ch = self._channel_to_mask(channel)
            if MAGICK_VERSION_NUMBER < 0x700:
                r = library.MagickSharpenImageChannel(self.wand,
                                                      channel_ch,
                                                      radius, sigma)
            else:  # pragma: no cover
                mask = library.MagickSetImageChannelMask(self.wand, channel_ch)
                r = library.MagickSharpenImage(self.wand, radius, sigma)
                library.MagickSetImageChannelMask(self.wand, mask)
        return r

    @manipulative
    @trap_exception
    def shave(self, columns=0, rows=0):
        """Remove pixels from the edges.

        :param columns: amount to shave off the x-axis.
        :type columns: :class:`numbers.Integral`
        :param rows: amount to shave off the y-axis.
        :type rows: :class:`numbers.Integral`

        .. versionadded:: 0.5.0
        """
        assertions.assert_integer(columns=columns, row=rows)
        return library.MagickShaveImage(self.wand, columns, rows)

    @manipulative
    @trap_exception
    def shear(self, background='WHITE', x=0.0, y=0.0):
        """Shears the image to create a parallelogram, and fill the space
        created with a ``background`` color.

        :param background: Color to fill the void created by shearing the
                           image.
        :type background: :class:`wand.color.Color`
        :param x: Slide the image along the X-axis.
        :type x: :class:`numbers.Real`
        :param y: Slide the image along the Y-axis.
        :type y: :class:`numbers.Real`

        .. versionadded:: 0.5.4
        """
        if isinstance(background, string_type):
            background = Color(background)
        assertions.assert_color(background=background)
        assertions.assert_real(x=x, y=y)
        with background:
            r = library.MagickShearImage(self.wand, background.resource, x, y)
        return r

    @manipulative
    @trap_exception
    def sigmoidal_contrast(self, sharpen=True, strength=0.0, midpoint=0.0,
                           channel=None):
        """Modifies the contrast of the image by applying non-linear sigmoidal
        algorithm.

        .. code:: python

            with Image(filename='photo.jpg') as img:
                img.sigmoidal_contrast(sharpen=True,
                                       strength=3,
                                       midpoint=0.65 * img.quantum_range)

        :param sharpen: Increase the contrast when ``True`` (default), else
                        reduces contrast.
        :type sharpen: :class:`bool`
        :param strength: How much to adjust the contrast. Where a value of
                         ``0.0`` has no effect, ``3.0`` is typical, and
                         ``20.0`` is extreme.
        :type strength: :class:`numbers.Real`
        :param midpoint: Normalized value between `0.0` & :attr:`quantum_range`
        :type midpoint: :class:`numbers.Real`
        :param channel: Optional color channel to target. See
                        :const:`CHANNELS`.
        :type channel: :class:`basestring`

        .. versionadded:: 0.5.4

        .. versionchanged:: 0.5.5
           Added ``channel`` argument.
        """
        assertions.assert_bool(sharpen=sharpen)
        assertions.assert_real(strength=strength, midpoint=midpoint)
        if channel is None:
            r = library.MagickSigmoidalContrastImage(self.wand,
                                                     sharpen,
                                                     strength,
                                                     midpoint)
        else:
            channel_ch = self._channel_to_mask(channel)
            if MAGICK_VERSION_NUMBER < 0x700:
                r = library.MagickSigmoidalContrastImageChannel(
                    self.wand, channel_ch, sharpen, strength, midpoint
                )
            else:  # pragma: no cover
                mask = library.MagickSetImageChannelMask(self.wand, channel_ch)
                r = library.MagickSigmoidalContrastImage(self.wand,
                                                         sharpen,
                                                         strength,
                                                         midpoint)
                library.MagickSetImageChannelMask(self.wand, mask)
        return r

    def similarity(self, reference, threshold=0.0, metric='undefined'):
        """Scan image for best matching ``reference`` image, and
        return location & similarity.

        .. code:: python

            from wand.image import Image

            with Image(filename='subject.jpg') as img:
                with Image(filename='object.jpg') as reference:
                    location, diff = img.similarity(reference)
                    if diff == 0.0:
                        print('Exact match @ {left}x{top}'.format(**location))
                    elif diff < 0.1:
                        print('Close match @ {left}x{top}'.format(**location))
                    else:
                        # Difference not meaningful.
                        print('Not found')

        .. warning::

            This operation can be slow to complete.

        :param reference: Image to search for.
        :type reference: :class:`wand.image.Image`
        :param threshold: Stop scanning if reference similarity is below
                          given threshold. Default is ``0.0``.
        :type threshold: :class:`numbers.Real`
        :param metric: specify which comparison algorithm to use. See
                       :const:`COMPARE_METRICS` for a list of values.
                       Only used by ImageMagick-7.
        :type metric: :class:`basestring`
        :returns: List of location & similarity value. Location being a
                  dictionary of ``width``, ``height``, ``left``, & ``top``.
                  The similarity value is the compare distance, so a value of
                  ``0.0`` means an exact match.
        :rtype: :class:`tuple` (:class:`dict`, :class:`numbers.Real`)

        .. versionadded:: 0.5.4
        """
        assertions.assert_real(threshold=threshold)
        if not isinstance(reference, BaseImage):
            raise TypeError('reference must be in instance of '
                            'wand.image.Image, not ' + repr(reference))
        rio = RectangleInfo(0, 0, 0, 0)
        diff = ctypes.c_double(0.0)
        if MAGICK_VERSION_NUMBER < 0x700:
            artifact_value = binary(str(threshold))  # FIXME
            library.MagickSetImageArtifact(self.wand,
                                           b'compare:similarity-threshold',
                                           artifact_value)
            r = library.MagickSimilarityImage(self.wand,
                                              reference.wand,
                                              ctypes.byref(rio),
                                              ctypes.byref(diff))
        else:  # pragma: no cover
            assertions.string_in_list(COMPARE_METRICS,
                                      'wand.image.COMPARE_METRICS',
                                      metric=metric)
            metric_idx = COMPARE_METRICS.index(metric)
            r = library.MagickSimilarityImage(self.wand,
                                              reference.wand,
                                              metric_idx,
                                              threshold,
                                              ctypes.byref(rio),
                                              ctypes.byref(diff))
        if not r:  # pragma: no cover
            self.raise_exception()
        else:
            r = library.DestroyMagickWand(r)
        location = dict(width=rio.width, height=rio.height,
                        top=rio.y, left=rio.x)
        return (location, diff.value)

    @manipulative
    @trap_exception
    def sketch(self, radius=0.0, sigma=0.0, angle=0.0):
        """Simulates a pencil sketch effect. For best results, ``radius``
        value should be larger than ``sigma``.

        :param radius: size of Gaussian apature.
        :type radius: :class:`numbers.Real`
        :param sigma: standard deviation of the Gaussian operator.
        :type sigma: :class:`numbers.Real`
        :param angle: direction of blur.
        :type angle: :class:`numbers.Real`

        .. versionadded:: 0.5.3
        """
        assertions.assert_real(radius=radius, sigma=sigma, angle=angle)
        return library.MagickSketchImage(self.wand, radius, sigma, angle)

    def smush(self, stacked=False, offset=0):
        """Appends all images together. Similar behavior to :meth:`concat`,
        but with an optional offset between images.

        :param stacked: If True, will join top-to-bottom. If False, join images
                        from left-to-right (default).
        :type stacked: :class:`bool`
        :param offset: Minimum space (in pixels) between each join.
        :type offset: :class:`numbers.Integral`

        .. versionadded:: 0.5.3
        """
        assertions.assert_integer(offset=offset)
        library.MagickResetIterator(self.wand)
        result = library.MagickSmushImages(self.wand, bool(stacked), offset)
        if result:
            self.wand = result
        else:  # pragma: no cover
            self.raise_exception()

    @manipulative
    @trap_exception
    def solarize(self, threshold=0.0, channel=None):
        """Simulates extreme overexposure.

        :param threshold: between ``0.0`` and :attr:`quantum_range`.
        :type threshold: :class:`numbers.Real`
        :param channel: Optional color channel to target. See
                        :const:`CHANNELS`
        :type channel: :class:`basestring`

        .. versionadded:: 0.5.3

        .. versionchanged:: 0.5.5
           Added ``channel`` argument.
        """
        assertions.assert_real(threshold=threshold)
        if channel is None:
            r = library.MagickSolarizeImage(self.wand, threshold)
        else:
            channel_ch = self._channel_to_mask(channel)
            if MAGICK_VERSION_NUMBER < 0x700:
                r = library.MagickSolarizeImageChannel(self.wand,
                                                       channel_ch,
                                                       threshold)
            else:  # pragma: no cover
                mask = library.MagickSetImageChannelMask(self.wand, channel_ch)
                r = library.MagickSolarizeImage(self.wand, threshold)
                library.MagickSetImageChannelMask(self.wand, mask)
        return r

    @manipulative
    @trap_exception
    def sparse_color(self, method, colors, channel_mask=0x7):
        """Interpolates color values between points on an image.

        The ``colors`` argument should be a dict mapping
        :class:`~wand.color.Color` keys to coordinate tuples.

        For example::

            from wand.color import Color
            from wand.image import Image

            colors = {
                Color('RED'): (10, 50),
                Color('YELLOW'): (174, 32),
                Color('ORANGE'): (74, 123)
            }
            with Image(filename='input.png') as img:
                img.sparse_colors('bilinear', colors)

        The available interpolate methods are:

        - ``'barycentric'``
        - ``'bilinear'``
        - ``'shepards'``
        - ``'voronoi'``
        - ``'inverse'``
        - ``'manhattan'``

        You can control which color channels are effected by building a custom
        channel mask. For example::

            from wand.image import Image, CHANNELS

            with Image(filename='input.png') as img:
                colors = {
                    img[50, 50]: (50, 50),
                    img[100, 50]: (100, 50),
                    img[50, 75]: (50, 75),
                    img[100, 100]: (100, 100)
                }
                # Only apply Voronoi to Red & Alpha channels
                mask = CHANNELS['red'] | CHANNELS['alpha']
                img.sparse_colors('voronoi', colors, channel_mask=mask)

        :param method: Interpolate method. See :const:`SPARSE_COLOR_METHODS`
        :type method: :class:`basestring`
        :param colors: A dictionary of :class:`~wand.color.Color` keys mapped
                       to an (x, y) coordinate tuple.
        :type colors: :class:`abc.Mapping`
                      { :class:`~wand.color.Color`: (int, int) }
        :param channel_mask: Isolate specific color channels to apply
                             interpolation. Default to RGB channels.
        :type channel_mask: :class:`numbers.Integral`

        .. versionadded:: 0.5.3
        """
        assertions.string_in_list(SPARSE_COLOR_METHODS,
                                  'wand.image.SPARSE_COLOR_METHODS',
                                  method=method)
        if not isinstance(colors, abc.Mapping):
            raise TypeError('Colors must be a dict, not' + repr(colors))
        assertions.assert_unsigned_integer(channel_mask=channel_mask)
        method_idx = SPARSE_COLOR_METHODS[method]
        arguments = list()
        for color, point in colors.items():
            if isinstance(color, string_type):
                color = Color(color)
            x, y = point
            arguments.append(x)
            arguments.append(y)
            with color as c:
                if channel_mask & CHANNELS['red']:
                    arguments.append(c.red)
                if channel_mask & CHANNELS['green']:
                    arguments.append(c.green)
                if channel_mask & CHANNELS['blue']:
                    arguments.append(c.blue)
                if channel_mask & CHANNELS['alpha']:
                    arguments.append(c.alpha)
        argc = len(arguments)
        args = (ctypes.c_double * argc)(*arguments)
        if MAGICK_VERSION_NUMBER < 0x700:
            r = library.MagickSparseColorImage(self.wand,
                                               channel_mask,
                                               method_idx,
                                               argc,
                                               args)
        else:  # pragma: no cover
            # Set active channel, and capture mask to restore.
            channel_mask = library.MagickSetImageChannelMask(self.wand,
                                                             channel_mask)
            r = library.MagickSparseColorImage(self.wand,
                                               method_idx,
                                               argc,
                                               args)
            # Restore original state of channels
            library.MagickSetImageChannelMask(self.wand, channel_mask)
        return r

    @manipulative
    @trap_exception
    def splice(self, width=None, height=None, x=None, y=None):
        """Partitions image by splicing a ``width`` x ``height`` rectangle at
        (``x``, ``y``) offset coordinate. The space inserted will be replaced
        by the :attr:`background_color` value.

        :param width: number of pixel columns.
        :type width: :class:`numbers.Integral`
        :param height: number of pixel rows.
        :type height: :class:`numbers.Integral`
        :param x: offset on the X-axis.
        :type x: :class:`numbers.Integral`
        :param y: offset on the Y-axis.
        :type y: :class:`numbers.Integral`

        .. versionadded:: 0.5.3
        """
        assertions.assert_integer(width=width, height=height, x=x, y=y)
        return library.MagickSpliceImage(self.wand, width, height, x, y)

    @manipulative
    @trap_exception
    def spread(self, radius, method='undefined'):
        """Randomly displace pixels within a defined radius.

        :param radius: Distance a pixel can be displaced from source.
        :type radius: :class:`numbers.Real`
        :param method: Interpolation method. Only available with ImageMagick-7.
                       See :const:`PIXEL_INTERPOLATE_METHODS`.
        """
        assertions.assert_real(radius=radius)
        assertions.string_in_list(PIXEL_INTERPOLATE_METHODS,
                                  'wand.image.PIXEL_INTERPOLATE_METHODS',
                                  method=method)
        method_idx = PIXEL_INTERPOLATE_METHODS.index(method)
        if MAGICK_VERSION_NUMBER < 0x700:
            r = library.MagickSpreadImage(self.wand, radius)
        else:  # pragma: no cover
            r = library.MagickSpreadImage(self.wand, method_idx, radius)
        return r

    @manipulative
    def stegano(self, watermark, offset=0):
        """Hide a digital watermark of an image within the image.

        .. code-block:: python

            from wand.image import Image

            # Embed watermark
            with Image(filename='source.png') as img:
                with Image(filename='gray_watermark.png') as watermark:
                    print('watermark size (for recovery)', watermark.size)
                    img.stegano(watermark)
                img.save(filename='public.png')

            # Recover watermark
            with Image(width=w, height=h, pseudo='stegano:public.png') as img:
                img.save(filename='recovered_watermark.png')

        :param watermark: Image to hide within image.
        :type watermark: :class:`wand.image.Image`
        :param offset: Start embedding image after a number of pixels.
        :type offset: :class:`numbers.Integral`

        .. versionadded:: 0.5.4
        """
        if not isinstance(watermark, BaseImage):
            raise TypeError('Watermark image must be in instance of '
                            'wand.image.Image, not ' + repr(watermark))
        assertions.assert_integer(offset=offset)
        new_wand = library.MagickSteganoImage(self.wand, watermark.wand,
                                              offset)
        if new_wand:
            self.wand = new_wand
        else:  # pragma: no cover
            self.raise_exception()

    @manipulative
    @trap_exception
    def statistic(self, stat='undefined', width=None, height=None,
                  channel=None):
        """Replace each pixel with the statistic results from neighboring pixel
        values. The ``width`` & ``height`` defines the size, or apature, of
        the neighboring pixels.

        :param stat: The type of statistic to calculate. See
                     :const:`STATISTIC_TYPES`.
        :type stat: :class:`basestring`
        :param width: The size of neighboring pixels on the X-axis.
        :type width: :class:`numbers.Integral`
        :param height: The size of neighboring pixels on the Y-axis.
        :type height: :class:`numbers.Integral`
        :param channel: Optional color channel to target. See
                        :const:`CHANNELS`
        :type channel: :class:`basestring`

        .. versionadded:: 0.5.3

        .. versionchanged:: 0.5.5
           Added optional ``channel`` argument.
        """
        assertions.string_in_list(STATISTIC_TYPES,
                                  'wand.image.STATISTIC_TYPES',
                                  statistic=stat)
        assertions.assert_integer(width=width, height=height)
        stat_idx = STATISTIC_TYPES.index(stat)
        if channel is None:
            r = library.MagickStatisticImage(self.wand, stat_idx,
                                             width, height)
        else:
            channel_ch = self._channel_to_mask(channel)
            if MAGICK_VERSION_NUMBER < 0x700:
                r = library.MagickStatisticImageChannel(self.wand,
                                                        channel_ch,
                                                        stat_idx,
                                                        width,
                                                        height)
            else:  # pragma: no cover
                mask = library.MagickSetImageChannelMask(self.wand,
                                                         channel_ch)
                r = library.MagickStatisticImage(self.wand, stat_idx,
                                                 width, height)
                library.MagickSetImageChannelMask(self.wand, mask)
        return r

    @trap_exception
    def strip(self):
        """Strips an image of all profiles and comments.

        .. versionadded:: 0.2.0
        """
        return library.MagickStripImage(self.wand)

    @manipulative
    def texture(self, tile):
        """Repeat tile-image across the width & height of the image.

        .. code:: python

            from wand.image import Image

            with Image(width=100, height=100) as canvas:
                with Image(filename='tile.png') as tile:
                    canvas.texture(tile)
                canvas.save(filename='output.png')

        :param tile: image to repeat across canvas.
        :type tile: :class:`Image <wand.image.BaseImage>`

        .. versionadded:: 0.5.4
        """
        if not isinstance(tile, BaseImage):
            raise TypeError('Tile image must be an instance of '
                            'wand.image.Image, not ' + repr(tile))
        r = library.MagickTextureImage(self.wand, tile.wand)
        if not bool(r):  # pragma: no cover
            self.raise_exception()
        else:
            self.wand = r

    @manipulative
    @trap_exception
    def threshold(self, threshold=0.5, channel=None):
        """Changes the value of individual pixels based on the intensity
        of each pixel compared to threshold. The result is a high-contrast,
        two color image. It manipulates the image in place.

        :param threshold: threshold as a factor of quantum
        :type threshold: :class:`numbers.Real`
        :param channel: the channel type.  available values can be found
                        in the :const:`CHANNELS` mapping.  If ``None``,
                        threshold all channels.
        :type channel: :class:`basestring`

        .. versionadded:: 0.3.10

        """
        assertions.assert_real(threshold=threshold)
        if channel is None:
            r = library.MagickThresholdImage(self.wand,
                                             threshold * self.quantum_range)
        else:
            ch_const = self._channel_to_mask(channel)
            r = library.MagickThresholdImageChannel(
                self.wand, ch_const,
                threshold * self.quantum_range
            )
        return r

    @manipulative
    @trap_exception
    def thumbnail(self, width=None, height=None):
        """Changes the size of an image to the given dimensions and removes any
        associated profiles.  The goal is to produce small low cost thumbnail
        images suited for display on the

        :param width: the width in the scaled image. default is the original
                      width
        :type width: :class:`numbers.Integral`
        :param height: the height in the scaled image. default is the original
                       height
        :type height: :class:`numbers.Integral`

        .. versionadded:: 0.5.4
        """
        if width is None:
            width = self.width
        if height is None:
            height = self.height
        assertions.assert_unsigned_integer(width=width, height=height)
        return library.MagickThumbnailImage(self.wand, width, height)

    @manipulative
    @trap_exception
    def tint(self, color=None, alpha=None):
        """Applies a color vector to each pixel in the image.

        :param color: Color to calculate midtone.
        :type color: :class:`~wand.color.Color`
        :param alpha: Determine how to blend.
        :type alpha: :class:`~wand.color.Color`

        .. versionadded:: 0.5.3
        """
        if isinstance(color, string_type):
            color = Color(color)
        if isinstance(alpha, string_type):
            alpha = Color(alpha)
        assertions.assert_color(color=color, alpha=alpha)
        with color:
            with alpha:
                r = library.MagickTintImage(self.wand,
                                            color.resource,
                                            alpha.resource)
        return r

    @manipulative
    def transform(self, crop='', resize=''):
        """Transforms the image using :c:func:`MagickTransformImage`,
        which is a convenience function accepting geometry strings to
        perform cropping and resizing.  Cropping is performed first,
        followed by resizing.  Either or both arguments may be omitted
        or given an empty string, in which case the corresponding action
        will not be performed. Geometry specification strings are
        defined as follows:

        A geometry string consists of a size followed by an optional offset.
        The size is specified by one of the options below,
        where **bold** terms are replaced with appropriate integer values:

        **scale**\ ``%``
          Height and width both scaled by specified percentage

        **scale-x**\ ``%x``\ \ **scale-y**\ ``%``
          Height and width individually scaled by specified percentages.
          Only one % symbol is needed.

        **width**
          Width given, height automagically selected to preserve aspect ratio.

        ``x``\ \ **height**
          Height given, width automagically selected to preserve aspect ratio.

        **width**\ ``x``\ **height**
          Maximum values of width and height given; aspect ratio preserved.

        **width**\ ``x``\ **height**\ ``!``
          Width and height emphatically given; original aspect ratio ignored.

        **width**\ ``x``\ **height**\ ``>``
          Shrinks images with dimension(s) larger than the corresponding
          width and/or height dimension(s).

        **width**\ ``x``\ **height**\ ``<``
          Enlarges images with dimensions smaller than the corresponding
          width and/or height dimension(s).

        **area**\ ``@``
          Resize image to have the specified area in pixels.
          Aspect ratio is preserved.

        The offset, which only applies to the cropping geometry string,
        is given by ``{+-}``\ **x**\ ``{+-}``\ **y**\ , that is,
        one plus or minus sign followed by an **x** offset,
        followed by another plus or minus sign, followed by a **y** offset.
        Offsets are in pixels from the upper left corner of the image.
        Negative offsets will cause the corresponding number of pixels to
        be removed from the right or bottom edge of the image, meaning the
        cropped size will be the computed size minus the absolute value
        of the offset.

        For example, if you want to crop your image to 300x300 pixels
        and then scale it by 2x for a final size of 600x600 pixels,
        you can call::

            image.transform('300x300', '200%')

        This method is a fairly thin wrapper for the C API, and does not
        perform any additional checking of the parameters except insofar as
        verifying that they are of the correct type.  Thus, like the C
        API function, the method is very permissive in terms of what
        it accepts for geometry strings; unrecognized strings and
        trailing characters will be ignored rather than raising an error.

        :param crop: A geometry string defining a subregion of the image
                     to crop to
        :type crop: :class:`basestring`
        :param resize: A geometry string defining the final size of the image
        :type resize: :class:`basestring`

        .. seealso::

           `ImageMagick Geometry Specifications`__
              Cropping and resizing geometry for the ``transform`` method are
              specified according to ImageMagick's geometry string format.
              The ImageMagick documentation provides more information about
              geometry strings.

           __ http://www.imagemagick.org/script/command-line-processing.php#geometry

        .. versionadded:: 0.2.2
        .. versionchanged:: 0.5.0
           Will call :meth:`crop()` followed by :meth:`resize()` in the event
           that :c:func:`MagickTransformImage` is not available.

        """  # noqa
        # Check that the values given are the correct types.  ctypes will do
        # this automatically, but we can make the error message more friendly
        # here.
        assertions.assert_string(crop=crop, resize=resize)
        # Also verify that only ASCII characters are included
        try:
            crop = crop.encode('ascii')
        except UnicodeEncodeError:
            raise ValueError('crop must only contain ascii-encodable ' +
                             'characters.')
        try:
            resize = resize.encode('ascii')
        except UnicodeEncodeError:
            raise ValueError('resize must only contain ascii-encodable ' +
                             'characters.')
        if not library.MagickTransformImage:  # pragma: no cover
            # Method removed from ImageMagick-7.
            if crop:
                x = ctypes.c_ssize_t(0)
                y = ctypes.c_ssize_t(0)
                width = ctypes.c_size_t(self.width)
                height = ctypes.c_size_t(self.height)
                libmagick.GetGeometry(crop,
                                      ctypes.byref(x),
                                      ctypes.byref(y),
                                      ctypes.byref(width),
                                      ctypes.byref(height))
                self.crop(top=y.value,
                          left=x.value,
                          width=width.value,
                          height=height.value,
                          reset_coords=False)
            if resize:
                x = ctypes.c_ssize_t()
                y = ctypes.c_ssize_t()
                width = ctypes.c_size_t(self.width)
                height = ctypes.c_size_t(self.height)
                libmagick.ParseMetaGeometry(resize,
                                            ctypes.byref(x),
                                            ctypes.byref(y),
                                            ctypes.byref(width),
                                            ctypes.byref(height))
                self.resize(width=width.value,
                            height=height.value)
            # Both `BaseImage.crop` & `BaseImage.resize` will handle
            # animation & error handling, so we can stop here.
            return None
        if self.animation:
            new_wand = library.MagickCoalesceImages(self.wand)
            length = len(self.sequence)
            for i in xrange(length):
                library.MagickSetIteratorIndex(new_wand, i)
                if i:
                    library.MagickAddImage(
                        new_wand,
                        library.MagickTransformImage(new_wand, crop, resize)
                    )
                else:
                    new_wand = library.MagickTransformImage(new_wand,
                                                            crop,
                                                            resize)
            self.sequence.instances = []
        else:
            new_wand = library.MagickTransformImage(self.wand, crop, resize)
        if not new_wand:  # pragma: no cover
            self.raise_exception()
        self.wand = new_wand

    @manipulative
    @trap_exception
    def transform_colorspace(self, colorspace_type):
        """Transform image's colorspace.

        :param colorspace_type: colorspace_type. available value can be found
                                in the :const:`COLORSPACE_TYPES`
        :type colorspace_type: :class:`basestring`

        .. versionadded:: 0.4.2

        """
        assertions.string_in_list(COLORSPACE_TYPES,
                                  'wand.image.COLORSPACE_TYPES',
                                  colorspace=colorspace_type)
        return library.MagickTransformImageColorspace(
            self.wand,
            COLORSPACE_TYPES.index(colorspace_type)
        )

    @manipulative
    @trap_exception
    def transparent_color(self, color, alpha, fuzz=0, invert=False):
        """Makes the color ``color`` a transparent color with a tolerance of
        fuzz. The ``alpha`` parameter specify the transparency level and the
        parameter ``fuzz`` specify the tolerance.

        :param color: The color that should be made transparent on the image,
                      color object
        :type color: :class:`wand.color.Color`
        :param alpha: the level of transparency: 1.0 is fully opaque
                      and 0.0 is fully transparent.
        :type alpha: :class:`numbers.Real`
        :param fuzz: By default target must match a particular pixel color
                     exactly. However, in many cases two colors may differ
                     by a small amount. The fuzz member of image defines how
                     much tolerance is acceptable to consider two colors as the
                     same. For example, set fuzz to 10 and the color red at
                     intensities of 100 and 102 respectively are now
                     interpreted as the same color for the color.
        :type fuzz: :class:`numbers.Integral`
        :param invert: Boolean to tell to paint the inverse selection.
        :type invert: :class:`bool`

        .. versionadded:: 0.3.0

        """
        assertions.assert_real(alpha=alpha)
        assertions.assert_integer(fuzz=fuzz)
        if isinstance(color, string_type):
            color = Color(color)
        assertions.assert_color(color=color)
        with color:
            r = library.MagickTransparentPaintImage(self.wand, color.resource,
                                                    alpha, fuzz, invert)
        return r

    @manipulative
    def transparentize(self, transparency):
        """Makes the image transparent by subtracting some percentage of
        the black color channel.  The ``transparency`` parameter specifies the
        percentage.

        :param transparency: the percentage fade that should be performed on
                             the image, from 0.0 to 1.0
        :type transparency: :class:`numbers.Real`

        .. versionadded:: 0.2.0

        """
        if transparency:
            t = ctypes.c_double(float(self.quantum_range *
                                      float(transparency)))
            if t.value > self.quantum_range or t.value < 0:
                raise ValueError('transparency must be a numbers.Real value ' +
                                 'between 0.0 and 1.0')
            # Set the wand to image zero, in case there are multiple images
            # in it
            library.MagickSetIteratorIndex(self.wand, 0)
            # Change the pixel representation of the image
            # to RGB with an alpha channel
            if MAGICK_VERSION_NUMBER < 0x700:
                image_type = 'truecolormatte'
            else:  # pragma: no cover
                image_type = 'truecoloralpha'
            library.MagickSetImageType(self.wand,
                                       IMAGE_TYPES.index(image_type))
            # Perform the black channel subtraction
            self.evaluate(operator='subtract',
                          value=t.value,
                          channel='opacity')
            self.raise_exception()

    @manipulative
    @trap_exception
    def transpose(self):
        """Creates a vertical mirror image by reflecting the pixels around
        the central x-axis while rotating them 90-degrees.

        .. versionadded:: 0.4.1
        """
        return library.MagickTransposeImage(self.wand)

    @manipulative
    @trap_exception
    def transverse(self):
        """Creates a horizontal mirror image by reflecting the pixels around
        the central y-axis while rotating them 270-degrees.

        .. versionadded:: 0.4.1
        """
        return library.MagickTransverseImage(self.wand)

    @manipulative
    @trap_exception
    def trim(self, color=None, fuzz=0):
        """Remove solid border from image. Uses top left pixel as a guide
        by default, or you can also specify the ``color`` to remove.

        :param color: the border color to remove.
                      if it's omitted top left pixel is used by default
        :type color: :class:`~wand.color.Color`
        :param fuzz: Defines how much tolerance is acceptable to consider
                     two colors as the same.
        :type fuzz: :class:`numbers.Integral`

        .. versionchanged:: 0.5.2
           The ``color`` parameter may except color-compliant strings.

        .. versionchanged:: 0.3.0
           Optional ``color`` and ``fuzz`` parameters.

        .. versionadded:: 0.2.1

        """
        if color is None:
            color = self[0, 0]
        elif isinstance(color, string_type):
            color = Color(color)
        assertions.assert_color(color=color)
        with color:
            self.border(color, 1, 1, compose="copy")
        return library.MagickTrimImage(self.wand, fuzz)

    @manipulative
    @trap_exception
    def unique_colors(self):
        """Discards all duplicate pixels, and rebuilds the image
        as a single row.

        .. versionadded:: 0.5.0
        """
        return library.MagickUniqueImageColors(self.wand)

    @manipulative
    @trap_exception
    def unsharp_mask(self, radius, sigma, amount, threshold, channel=None):
        """Sharpens the image using unsharp mask filter. We convolve the image
        with a Gaussian operator of the given ``radius`` and standard deviation
        (``sigma``). For reasonable results, ``radius`` should be larger than
        ``sigma``. Use a radius of 0 and :meth:`unsharp_mask()` selects
        a suitable radius for you.

        :param radius: the radius of the Gaussian, in pixels,
                       not counting the center pixel
        :type radius: :class:`numbers.Real`
        :param sigma: the standard deviation of the Gaussian, in pixels
        :type sigma: :class:`numbers.Real`
        :param amount: the percentage of the difference between the original
                       and the blur image that is added back into the original
        :type amount: :class:`numbers.Real`
        :param threshold: the threshold in pixels needed to apply
                          the diffence amount
        :type threshold: :class:`numbers.Real`
        :param channel: Optional color channel to target. See
                        :const:`CHANNELS`
        :type channel: :class:`basestring`

        .. versionadded:: 0.3.4

        .. versionchanged:: 0.5.5
           Added optional ``channel`` argument.
        """
        assertions.assert_real(radius=radius, sigma=sigma,
                               amount=amount, threshold=threshold)
        if channel is None:
            r = library.MagickUnsharpMaskImage(self.wand, radius, sigma,
                                               amount, threshold)
        else:
            channel_ch = self._channel_to_mask(channel)
            if MAGICK_VERSION_NUMBER < 0x700:
                r = library.MagickUnsharpMaskImageChannel(
                    self.wand, channel_ch, radius, sigma, amount, threshold
                )
            else:  # pragma: no cover
                mask = library.MagickSetImageChannelMask(self.wand, channel_ch)
                r = library.MagickUnsharpMaskImage(self.wand, radius, sigma,
                                                   amount, threshold)
                library.MagickSetImageChannelMask(self.wand, mask)
        return r

    @manipulative
    @trap_exception
    def vignette(self, radius=0.0, sigma=0.0, x=0, y=0):
        """Creates a soft vignette style effect on the image.

        :param radius: the radius of the Gaussian blur effect.
        :type radius: :class:`numbers.Real`
        :param sigma: the standard deviation of the Gaussian effect.
        :type sigma: :class:`numbers.Real`
        :param x: Width of the oval effect.
        :type x: :class:`numbers.Integral`
        :param y: Height of the oval effect.
        :type y: :class:`numbers.Integral`

        .. versionadded:: 0.5.2
        """
        assertions.assert_real(radius=radius, sigma=sigma)
        return library.MagickVignetteImage(self.wand, radius, sigma, x, y)

    @manipulative
    def watermark(self, image, transparency=0.0, left=0, top=0):
        """Transparentized the supplied ``image`` and places it over the
        current image, with the top left corner of ``image`` at coordinates
        ``left``, ``top`` of the current image.  The dimensions of the
        current image are not changed.

        :param image: the image placed over the current image
        :type image: :class:`wand.image.Image`
        :param transparency: the percentage fade that should be performed on
                             the image, from 0.0 to 1.0
        :type transparency: :class:`numbers.Real`
        :param left: the x-coordinate where `image` will be placed
        :type left: :class:`numbers.Integral`
        :param top: the y-coordinate where `image` will be placed
        :type top: :class:`numbers.Integral`

        .. versionadded:: 0.2.0

        """
        with image.clone() as watermark_image:
            watermark_image.transparentize(transparency)
            watermark_image.clamp()
            self.composite(watermark_image, left=left, top=top)
        self.raise_exception()

    @manipulative
    @trap_exception
    def wave(self, amplitude=0.0, wave_length=0.0, method='undefined'):
        """Creates a ripple effect within the image.

        :param amplitude: height of wave form.
        :type amplitude: :class:`numbers.Real`
        :param wave_length: width of wave form.
        :type wave_length: :class:`numbers.Real`
        :param method: pixel interpolation method. Only available with
                       ImageMagick-7. See :const:`PIXEL_INTERPOLATE_METHODS`
        :type method: :class:`basestring`

        .. versionadded:: 0.5.2
        """
        assertions.assert_real(amplitude=amplitude, wave_length=wave_length)
        assertions.string_in_list(PIXEL_INTERPOLATE_METHODS,
                                  'wand.image.PIXEL_INTERPOLATE_METHODS',
                                  method=method)
        if MAGICK_VERSION_NUMBER < 0x700:
            r = library.MagickWaveImage(self.wand, amplitude, wave_length)
        else:  # pragma: no cover
            method_idx = PIXEL_INTERPOLATE_METHODS.index(method)
            r = library.MagickWaveImage(self.wand, amplitude, wave_length,
                                        method_idx)
        return r

    @manipulative
    @trap_exception
    def wavelet_denoise(self, threshold=0.0, softness=0.0):
        """Removes noise by applying a `wavelet transform`_.

        .. _`wavelet transform`:
           https://en.wikipedia.org/wiki/Wavelet_transform

        .. warning::

            This class method is only available with ImageMagick 7.0.8-41, or
            greater.

        :param threshold: Smoothing limit.
        :type threshold: :class:`numbers.Real`
        :param softness: Attenuate of the smoothing threshold.
        :type softness: :class:`numbers.Real`
        :raises WandLibraryVersionError: If system's version of ImageMagick
                                         does not support this method.

        .. versionadded:: 0.5.5
        """
        if library.MagickWaveletDenoiseImage is None:
            msg = 'Method requires ImageMagick version 7.0.8-41 or greater.'
            raise WandLibraryVersionError(msg)
        assertions.assert_real(threshold=threshold, softness=softness)
        if 0.0 < threshold <= 1.0:
            threshold *= self.quantum_range
        if 0.0 < softness <= 1.0:
            softness *= self.quantum_range
        return library.MagickWaveletDenoiseImage(self.wand, threshold,
                                                 softness)

    @manipulative
    @trap_exception
    def white_threshold(self, threshold):
        """Forces all pixels above a given color as white. Leaves pixels
        below threshold unaltered.

        :param threshold: Color to be referenced as a threshold.
        :type threshold: :class:`Color`

        .. versionadded:: 0.5.2
        """
        if isinstance(threshold, string_type):
            threshold = Color(threshold)
        assertions.assert_color(threshold=threshold)
        with threshold:
            r = library.MagickWhiteThresholdImage(self.wand,
                                                  threshold.resource)
        return r


class Image(BaseImage):
    """An image object.

    :param image: makes an exact copy of the ``image``
    :type image: :class:`Image`
    :param blob: opens an image of the ``blob`` byte array
    :type blob: :class:`bytes`
    :param file: opens an image of the ``file`` object
    :type file: file object
    :param filename: opens an image of the ``filename`` string
    :type filename: :class:`basestring`
    :param format: forces filename to  buffer. ``format`` to help
                   ImageMagick detect the file format. Used only in
                   ``blob`` or ``file`` cases
    :type format: :class:`basestring`
    :param width: the width of new blank image or an image loaded from raw
                  data.
    :type width: :class:`numbers.Integral`
    :param height: the height of new blank image or an image loaded from
                   raw data.
    :type height: :class:`numbers.Integral`
    :param depth: the depth used when loading raw data.
    :type depth: :class:`numbers.Integral`
    :param background: an optional background color.
                       default is transparent
    :type background: :class:`wand.color.Color`
    :param resolution: set a resolution value (dpi),
                       useful for vectorial formats (like pdf)
    :type resolution: :class:`collections.abc.Sequence`,
                      :Class:`numbers.Integral`

    .. versionadded:: 0.1.5
       The ``file`` parameter.

    .. versionadded:: 0.1.1
       The ``blob`` parameter.

    .. versionadded:: 0.2.1
       The ``format`` parameter.

    .. versionadded:: 0.2.2
       The ``width``, ``height``, ``background`` parameters.

    .. versionadded:: 0.3.0
       The ``resolution`` parameter.

    .. versionadded:: 0.4.2
       The ``depth`` parameter.

    .. versionchanged:: 0.4.2
       The ``depth``, ``width`` and ``height`` parameters can be used
       with the ``filename``, ``file`` and ``blob`` parameters to load
       raw pixel data.

    .. versionadded:: 0.5.0
       The ``pseudo`` parameter.

    .. versionchanged:: 0.5.4
       Read constructor no longer sets "transparent" background by default.
       Use the ``background`` paramater to specify canvas color when reading
       in image.

    .. describe:: [left:right, top:bottom]

       Crops the image by its ``left``, ``right``, ``top`` and ``bottom``,
       and then returns the cropped one. ::

           with img[100:200, 150:300] as cropped:
               # manipulated the cropped image
               pass

       Like other subscriptable objects, default is 0 or its width/height::

           img[:, :]        #--> just clone
           img[:100, 200:]  #--> equivalent to img[0:100, 200:img.height]

       Negative integers count from the end (width/height)::

           img[-70:-50, -20:-10]
           #--> equivalent to img[width-70:width-50, height-20:height-10]

       :returns: the cropped image
       :rtype: :class:`Image`

       .. versionadded:: 0.1.2

    """

    #: (:class:`ArtifactTree`) A dict mapping to image artifacts.
    #: Similar to :attr:`metadata`, but used to alter behavior of various
    #: internal operations.
    #:
    #: .. versionadded:: 0.5.0
    artifacts = None

    #: (:class:`ChannelImageDict`) The mapping of separated channels
    #: from the image. ::
    #:
    #:     with image.channel_images['red'] as red_image:
    #:         display(red_image)
    channel_images = None

    #: (:class:`ChannelDepthDict`) The mapping of channels to their depth.
    #: Read only.
    #:
    #: .. versionadded:: 0.3.0
    channel_depths = None

    #: (:class:`Metadata`) The metadata mapping of the image.  Read only.
    #:
    #: .. versionadded:: 0.3.0
    metadata = None

    #: (:class:`ProfileDict`) The mapping of image profiles.
    #:
    #: .. versionadded:: 0.5.1
    profiles = None

    def __init__(self, image=None, blob=None, file=None, filename=None,
                 format=None, width=None, height=None, depth=None,
                 background=None, resolution=None, pseudo=None):
        new_args = width, height, background, depth
        open_args = blob, file, filename
        if any(a is not None for a in new_args) and image is not None:
            raise TypeError("blank image parameters can't be used with image "
                            'parameter')
        if sum(a is not None for a in open_args + (image,)) > 1:
            raise TypeError(', '.join(open_args) +
                            ' and image parameters are exclusive each other; '
                            'use only one at once')
        if not (format is None):
            if not isinstance(format, string_type):
                raise TypeError('format must be a string, not ' + repr(format))
            if not any(a is not None for a in open_args):
                raise TypeError('format can only be used with the blob, file '
                                'or filename parameter')
        if depth not in [None, 8, 16, 32]:
            raise ValueError('Depth must be 8, 16 or 32')
        with self.allocate():
            if image is None:
                wand = library.NewMagickWand()
                super(Image, self).__init__(wand)
            if image is not None:
                if not isinstance(image, BaseImage):
                    raise TypeError('image must be a wand.image.Image '
                                    'instance, not ' + repr(image))
                wand = library.CloneMagickWand(image.wand)
                super(Image, self).__init__(wand)
            elif any(a is not None for a in open_args):
                if format:
                    format = binary(format)
                if background:
                    if isinstance(background, string_type):
                        background = Color(background)
                    assertions.assert_color(background=background)
                    with background:
                        r = library.MagickSetBackgroundColor(
                            self.wand,
                            background.resource
                        )
                        if not r:
                            self.raise_exception()
                if width is not None and height is not None:
                    assertions.assert_counting_number(width=width,
                                                      height=height)
                    library.MagickSetSize(self.wand, width, height)
                if depth is not None:
                    library.MagickSetDepth(self.wand, depth)
                if format:
                    library.MagickSetFormat(self.wand, format)
                    if not filename:
                        library.MagickSetFilename(self.wand,
                                                  b'buffer.' + format)
                if file is not None:
                    self.read(file=file, resolution=resolution)
                elif blob is not None:
                    self.read(blob=blob, resolution=resolution)
                elif filename is not None:
                    self.read(filename=filename, resolution=resolution)
                # clear the wand format, otherwise any subsequent call to
                # MagickGetImageBlob will silently change the image to this
                # format again.
                library.MagickSetFormat(self.wand, binary(""))
            elif width is not None and height is not None:
                if pseudo is None:
                    self.blank(width, height, background)
                else:
                    self.pseudo(width, height, pseudo)
                if depth:
                    r = library.MagickSetImageDepth(self.wand, depth)
                    if not r:
                        raise self.raise_exception()
            self.metadata = Metadata(self)
            self.artifacts = ArtifactTree(self)
            from .sequence import Sequence
            self.sequence = Sequence(self)
            self.profiles = ProfileDict(self)
        self.raise_exception()

    def __repr__(self):
        return super(Image, self).__repr__(
            extra_format=' {self.format!r} ({self.width}x{self.height})'
        )

    def _repr_png_(self):
        with self.convert('png') as cloned:
            return cloned.make_blob()

    @classmethod
    def from_array(cls, array, channel_map=None, storage=None):
        """Create an image instance from a :mod:`numpy` array, or any other datatype
        that implements `__array_interface__`__ protocol.

        .. code::

            import numpy
            from wand.image import Image

            matrix = numpy.random.rand(100, 100, 3)
            with Image.from_array(matrix) as img:
                img.save(filename='noise.png')

        Use the optional ``channel_map`` & ``storage`` arguments to specify
        the order of color channels & data size. If ``channel_map`` is omitted,
        this method will will guess ``"RGB"``, ``"I"``, or ``"CMYK"`` based on
        array shape. If ``storage`` is omitted, this method will reference the
        array's ``typestr`` value, and raise a :class:`ValueError` if
        storage-type can not be mapped.

        Float values must be normalized between `0.0` and `1.0`, and signed
        integers should be converted to unsigned values between `0` and
        max value of type.

        Instances of :class:`Image` can also be exported to numpy arrays::

            with Image(filename='rose:') as img:
                matrix = numpy.array(img)

        __ https://docs.scipy.org/doc/numpy/reference/arrays.interface.html

        :param array: Numpy array of pixel values.
        :type array: :class:`numpy.array`
        :param channel_map: Color channel layout.
        :type channel_map: :class:`basestring`
        :param storage: Datatype per pixel part.
        :type storage: :class:`basestring`
        :returns: New instance of an image.
        :rtype: :class:`~wand.image.Image`

        .. versionadded:: 0.5.3
        """
        arr_itr = array.__array_interface__
        typestr = arr_itr['typestr']  # Required by interface.
        shape = arr_itr['shape']  # Required by interface.
        data_ptr, flag = arr_itr.get('data', (None, False))  # Optional
        strides = arr_itr.get('strides', None)  # Optional
        if storage is None:
            # Attempt to guess storage
            storage_map = dict(u1='char', i1='char',
                               u2='short', i2='short',
                               u4='integer', i4='integer',
                               u8='long', i8='integer',
                               f4='float', f8='double')
            for token in storage_map:
                if token in typestr:
                    storage = storage_map[token]
                    break
            if storage is None:
                raise ValueError('Unable to determine storage type.')
        if channel_map is None:
            # Attempt to guess channel map
            if len(shape) == 3:
                if shape[2] < 5:
                    channel_map = 'RGBA'[0:shape[2]]
                else:
                    channel_map = 'CMYKA'[0:shape[2]]
            else:
                channel_map = 'I'
        if data_ptr is None or strides is not None:
            data_ptr = array.ctypes.data_as(ctypes.c_void_p)
        storage_idx = STORAGE_TYPES.index(storage)
        width, height = shape[:2]
        wand = library.NewMagickWand()
        instance = cls(BaseImage(wand))
        r = library.MagickConstituteImage(instance.wand,
                                          width,
                                          height,
                                          binary(channel_map),
                                          storage_idx,
                                          data_ptr)
        if not r:
            instance.raise_exception(cls)
        return instance

    @classmethod
    def stereogram(cls, left, right):
        """Create a new stereogram image from two existing images.

        :param left: Left-eye image.
        :type left: :class:`wand.image.Image`
        :param right: Right-eye image.
        :type right: :class:`wand.image.Image`

        .. versionadded:: 0.5.4
        """
        if not isinstance(left, BaseImage):
            raise TypeError('Left image must be in instance of '
                            'wand.image.Image, not ' + repr(left))
        if not isinstance(right, BaseImage):
            raise TypeError('Right image must be in instance of '
                            'wand.image.Image, not ' + repr(right))
        wand = library.MagickStereoImage(left.wand, right.wand)
        if not wand:  # pragma: no cover
            left.raise_exception()
        return cls(BaseImage(wand))

    @property
    def animation(self):
        return (self.mimetype in ('image/gif', 'image/x-gif') and
                len(self.sequence) > 1)

    @property
    def mimetype(self):
        """(:class:`basestring`) The MIME type of the image
        e.g. ``'image/jpeg'``, ``'image/png'``.

        .. versionadded:: 0.1.7

        """
        rp = libmagick.MagickToMime(binary(self.format))
        if not bool(rp):
            self.raise_exception()
        mimetype = rp.value
        return text(mimetype)

    def blank(self, width, height, background=None):
        """Creates blank image.

        :param width: the width of new blank image.
        :type width: :class:`numbers.Integral`
        :param height: the height of new blank image.
        :type height: :class:`numbers.Integral`
        :param background: an optional background color.
                           default is transparent
        :type background: :class:`wand.color.Color`
        :returns: blank image
        :rtype: :class:`Image`

        .. versionadded:: 0.3.0

        """
        assertions.assert_counting_number(width=width, height=height)
        if background is None:
            background = Color('transparent')
        elif isinstance(background, string_type):
            background = Color(background)
        assertions.assert_color(background=background)
        with background:
            r = library.MagickNewImage(self.wand, width, height,
                                       background.resource)
            if not r:
                self.raise_exception()
        return self

    def clear(self):
        """Clears resources associated with the image, leaving the image blank,
        and ready to be used with new image.

        .. versionadded:: 0.3.0

        """
        library.ClearMagickWand(self.wand)

    def close(self):
        """Closes the image explicitly. If you use the image object in
        :keyword:`with` statement, it was called implicitly so don't have to
        call it.

        .. note::

           It has the same functionality of :attr:`destroy()` method.

        """
        self.destroy()

    def compare_layers(self, method):
        """Generates new images showing the delta pixels between
        layers. Similar pixels are converted to transparent.
        Useful for debugging complex animations. ::

            with img.compare_layers('compareany') as delta:
                delta.save(filename='framediff_%02d.png')

        .. note::

            May not work as expected if animations are already
            optimized.

        :param method: Can be ``'compareany'``,
                       ``'compareclear'``, or ``'compareoverlay'``
        :type method: :class:`basestring`
        :returns: new image stack.
        :rtype: :class:`Image`

        .. versionadded:: 0.5.0
        """
        if not isinstance(method, string_type):
            raise TypeError('method must be a string from IMAGE_LAYER_METHOD, '
                            'not ' + repr(method))
        if method not in ('compareany', 'compareclear', 'compareoverlay'):
            raise ValueError('method can only be \'compareany\', '
                             '\'compareclear\', or \'compareoverlay\'')
        r = None
        m = IMAGE_LAYER_METHOD.index(method)
        if MAGICK_VERSION_NUMBER >= 0x700:  # pragma: no cover
            r = library.MagickCompareImagesLayers(self.wand, m)
        elif library.MagickCompareImageLayers:
            r = library.MagickCompareImageLayers(self.wand, m)
        else:
            raise AttributeError('MagickCompareImageLayers method '
                                 'not available on system.')
        if not r:
            self.raise_exception()
        return Image(image=BaseImage(r))

    def convert(self, format):
        """Converts the image format with the original image maintained.
        It returns a converted image instance which is new. ::

            with img.convert('png') as converted:
                converted.save(filename='converted.png')

        :param format: image format to convert to
        :type format: :class:`basestring`
        :returns: a converted image
        :rtype: :class:`Image`
        :raises ValueError: when the given ``format`` is unsupported

        .. versionadded:: 0.1.6

        """
        cloned = self.clone()
        cloned.format = format
        return cloned

    def destroy(self):
        """Manually remove :class:`~.sequence.SingleImage`'s in
        the :class:`~.sequence.Sequence`, allowing it to
        be properly garbage collected after using a ``with Image()`` context
        manager.

        """
        while self.sequence:
            self.sequence.pop()
        super(Image, self).destroy()

    def make_blob(self, format=None):
        """Makes the binary string of the image.

        :param format: the image format to write e.g. ``'png'``, ``'jpeg'``.
                       it is omittable
        :type format: :class:`basestring`
        :returns: a blob (bytes) string
        :rtype: :class:`bytes`
        :raises ValueError: when ``format`` is invalid

        .. versionchanged:: 0.1.6
           Removed a side effect that changes the image :attr:`format`
           silently.

        .. versionadded:: 0.1.5
           The ``format`` parameter became optional.

        .. versionadded:: 0.1.1

        """
        if format is not None:
            with self.convert(format) as converted:
                return converted.make_blob()
        library.MagickResetIterator(self.wand)
        length = ctypes.c_size_t()
        blob_p = None
        if len(self.sequence) > 1:
            blob_p = library.MagickGetImagesBlob(self.wand,
                                                 ctypes.byref(length))
        else:
            blob_p = library.MagickGetImageBlob(self.wand,
                                                ctypes.byref(length))
        if blob_p and length.value:
            blob = ctypes.string_at(blob_p, length.value)
            library.MagickRelinquishMemory(blob_p)
            return blob
        else:  # pragma: no cover
            self.raise_exception()

    def pseudo(self, width, height, pseudo='xc:'):
        """Creates a new image from ImageMagick's internal protocol coders.

        :param width: Total columns of the new image.
        :type width: :class:`numbers.Integral`
        :param height: Total rows of the new image.
        :type height: :class:`numbers.Integral`
        :param pseudo: The protocol & arguments for the pseudo image.
        :type pseudo: :class:`basestring`

        .. versionadded:: 0.5.0
        """
        assertions.assert_counting_number(width=width, height=height)
        assertions.assert_string(pseudo=pseudo)
        r = library.MagickSetSize(self.wand, width, height)
        if not r:
            self.raise_exception()
        r = library.MagickReadImage(self.wand, encode_filename(pseudo))
        if not r:
            self.raise_exception()

    def read(self, file=None, filename=None, blob=None, resolution=None):
        """Read new image into Image() object.

        :param blob: reads an image from the ``blob`` byte array
        :type blob: :class:`bytes`
        :param file: reads an image from the ``file`` object
        :type file: file object
        :param filename: reads an image from the ``filename`` string
        :type filename: :class:`basestring`
        :param resolution: set a resolution value (DPI),
                           useful for vectorial formats (like PDF)
        :type resolution: :class:`collections.abc.Sequence`,
                          :class:`numbers.Integral`

        .. versionadded:: 0.3.0

        """
        r = None
        # Resolution must be set after image reading.
        if resolution is not None:
            if (isinstance(resolution, abc.Sequence) and
                    len(resolution) == 2):
                library.MagickSetResolution(self.wand, *resolution)
            elif isinstance(resolution, numbers.Integral):
                library.MagickSetResolution(self.wand, resolution, resolution)
            else:
                raise TypeError('resolution must be a (x, y) pair or an '
                                'integer of the same x/y')
        if file is not None:
            if (isinstance(file, file_types) and
                    hasattr(libc, 'fdopen') and hasattr(file, 'mode')):
                fd = libc.fdopen(file.fileno(), file.mode)
                r = library.MagickReadImageFile(self.wand, fd)
            elif not callable(getattr(file, 'read', None)):
                raise TypeError('file must be a readable file object'
                                ', but the given object does not '
                                'have read() method')
            else:
                blob = file.read()
                file = None
        if blob is not None:
            if not isinstance(blob, abc.Iterable):
                raise TypeError('blob must be iterable, not ' +
                                repr(blob))
            if not isinstance(blob, binary_type):
                blob = b''.join(blob)
            r = library.MagickReadImageBlob(self.wand, blob, len(blob))
        elif filename is not None:
            filename = encode_filename(filename)
            r = library.MagickReadImage(self.wand, filename)
        if not r:
            self.raise_exception()
            msg = ('MagickReadImage returns false, but did raise ImageMagick '
                   'exception. This can occurs when a delegate is missing, or '
                   'returns EXIT_SUCCESS without generating a raster.')
            raise WandRuntimeError(msg)

    def save(self, file=None, filename=None):
        """Saves the image into the ``file`` or ``filename``. It takes
        only one argument at a time.

        :param file: a file object to write to
        :type file: file object
        :param filename: a filename string to write to
        :type filename: :class:`basestring`

        .. versionadded:: 0.1.5
           The ``file`` parameter.

        .. versionadded:: 0.1.1

        """
        if file is None and filename is None:
            raise TypeError('expected an argument')
        elif file is not None and filename is not None:
            raise TypeError('expected only one argument; but two passed')
        elif file is not None:
            if isinstance(file, string_type):
                raise TypeError('file must be a writable file object, '
                                'but {0!r} is a string; did you want '
                                '.save(filename={0!r})?'.format(file))
            elif isinstance(file, file_types) and hasattr(libc, 'fdopen'):
                fd = libc.fdopen(file.fileno(), file.mode)
                if len(self.sequence) > 1:
                    r = library.MagickWriteImagesFile(self.wand, fd)
                else:
                    r = library.MagickWriteImageFile(self.wand, fd)
                libc.fflush(fd)
                if not r:
                    self.raise_exception()
            else:
                if not callable(getattr(file, 'write', None)):
                    raise TypeError('file must be a writable file object, '
                                    'but it does not have write() method: ' +
                                    repr(file))
                file.write(self.make_blob())
        else:
            if not isinstance(filename, string_type):
                raise TypeError('filename must be a string, not ' +
                                repr(filename))
            filename = encode_filename(filename)
            if len(self.sequence) > 1:
                r = library.MagickWriteImages(self.wand, filename, True)
            else:
                r = library.MagickWriteImage(self.wand, filename)
            if not r:
                self.raise_exception()


class Iterator(Resource, abc.Iterator):
    """Row iterator for :class:`Image`. It shouldn't be instantiated
    directly; instead, it can be acquired through :class:`Image` instance::

        assert isinstance(image, wand.image.Image)
        iterator = iter(image)

    It doesn't iterate every pixel, but rows. For example::

        for row in image:
            for col in row:
                assert isinstance(col, wand.color.Color)
                print(col)

    Every row is a :class:`collections.abc.Sequence` which consists of
    one or more :class:`wand.color.Color` values.

    :param image: the image to get an iterator
    :type image: :class:`Image`

    .. versionadded:: 0.1.3

    """

    c_is_resource = library.IsPixelIterator
    c_destroy_resource = library.DestroyPixelIterator
    c_get_exception = library.PixelGetIteratorException
    c_clear_exception = library.PixelClearIteratorException

    def __init__(self, image=None, iterator=None):
        if image is not None and iterator is not None:
            raise TypeError('it takes only one argument at a time')
        with self.allocate():
            if image is not None:
                if not isinstance(image, Image):
                    raise TypeError('expected a wand.image.Image instance, '
                                    'not ' + repr(image))
                self.resource = library.NewPixelIterator(image.wand)
                self.height = image.height
            else:
                if not isinstance(iterator, Iterator):
                    raise TypeError('expected a wand.image.Iterator instance, '
                                    'not ' + repr(iterator))
                self.resource = library.ClonePixelIterator(iterator.resource)
                self.height = iterator.height
        self.raise_exception()
        self.cursor = 0

    def __iter__(self):
        return self

    def seek(self, y):
        assertions.assert_unsigned_integer(seek=y)
        if y > self.height:
            raise ValueError('canot be greater than height')
        self.cursor = y
        if y == 0:
            library.PixelSetFirstIteratorRow(self.resource)
        else:
            if not library.PixelSetIteratorRow(self.resource, y - 1):
                self.raise_exception()

    def __next__(self, x=None):
        if self.cursor >= self.height:
            self.destroy()
            raise StopIteration()
        self.cursor += 1
        width = ctypes.c_size_t()
        pixels = library.PixelGetNextIteratorRow(self.resource,
                                                 ctypes.byref(width))
        if x is None:
            r_pixels = [None] * width.value
            for x in xrange(width.value):
                r_pixels[x] = Color.from_pixelwand(pixels[x])
            return r_pixels
        return Color.from_pixelwand(pixels[x])

    next = __next__  # Python 2 compatibility

    def clone(self):
        """Clones the same iterator.

        """
        return type(self)(iterator=self)


class ImageProperty(object):
    """The mixin class to maintain a weak reference to the parent
    :class:`Image` object.

    .. versionadded:: 0.3.0

    """

    def __init__(self, image):
        if not isinstance(image, BaseImage):
            raise TypeError('expected a wand.image.BaseImage instance, '
                            'not ' + repr(image))
        self._image = weakref.ref(image)

    @property
    def image(self):
        """(:class:`Image`) The parent image.

        It ensures that the parent :class:`Image`, which is held in a weak
        reference, still exists.  Returns the dereferenced :class:`Image`
        if it does exist, or raises a :exc:`ClosedImageError` otherwise.

        :exc: `ClosedImageError` when the parent Image has been destroyed

        """
        # Dereference our weakref and check that the parent Image stil exists
        image = self._image()
        if image is not None:
            return image
        raise ClosedImageError(
            'parent Image of {0!r} has been destroyed'.format(self)
        )


class OptionDict(ImageProperty, abc.MutableMapping):
    """Free-form mutable mapping of global internal settings.

    .. versionadded:: 0.3.0

    .. versionchanged:: 0.5.0
       Remove key check to :const:`OPTIONS`. Image properties are specific to
       vendor, and this library should not attempt to manage the 100+ options
       in a whitelist.
    """

    def __iter__(self):
        return iter(OPTIONS)

    def __len__(self):
        return len(OPTIONS)

    def __getitem__(self, key):
        assertions.assert_string(key=key)
        image = self.image
        return text(library.MagickGetOption(image.wand, binary(key)))

    def __setitem__(self, key, value):
        assertions.assert_string(key=key, value=value)
        image = self.image
        library.MagickSetOption(image.wand, binary(key), binary(value))

    def __delitem__(self, key):
        self[key] = ''


class Metadata(ImageProperty, abc.MutableMapping):
    """Class that implements dict-like read-only access to image metadata
    like EXIF or IPTC headers. Most WRITE encoders will ignore properties
    assigned here.

    :param image: an image instance
    :type image: :class:`Image`

    .. note::

       You don't have to use this by yourself.
       Use :attr:`Image.metadata` property instead.

    .. versionadded:: 0.3.0

    """

    def __init__(self, image):
        if not isinstance(image, Image):
            raise TypeError('expected a wand.image.Image instance, '
                            'not ' + repr(image))
        super(Metadata, self).__init__(image)

    def __getitem__(self, k):
        """
        :param k: Metadata header name string.
        :type k: :class:`basestring`
        :returns: a header value string
        :rtype: :class:`str`
        """
        assertions.assert_string(key=k)
        image = self.image
        v = library.MagickGetImageProperty(image.wand, binary(k))
        if bool(v) is False:
            raise KeyError(k)
        value = v.value
        return text(value)

    def __setitem__(self, k, v):
        """
        :param k: Metadata header name string.
        :type k: :class:`basestring`
        :param v: Value to assign.
        :type v: :class:`basestring`

        .. versionadded: 0.5.0
        """
        assertions.assert_string(key=k, value=v)
        image = self.image
        r = library.MagickSetImageProperty(image.wand, binary(k), binary(v))
        if not r:
            image.raise_exception()
        return v

    def __delitem__(self, k):
        """
        :param k: Metadata header name string.
        :type k: :class:`basestring`

        .. versionadded: 0.5.0
        """
        assertions.assert_string(key=k)
        image = self.image
        r = library.MagickDeleteImageProperty(image.wand, binary(k))
        if not r:
            image.raise_exception()

    def __iter__(self):
        image = self.image
        num = ctypes.c_size_t()
        props_p = library.MagickGetImageProperties(image.wand, b'', num)
        props = [text(props_p[i]) for i in xrange(num.value)]
        library.MagickRelinquishMemory(props_p)
        return iter(props)

    def __len__(self):
        image = self.image
        num = ctypes.c_size_t()
        props_p = library.MagickGetImageProperties(image.wand, b'', num)
        library.MagickRelinquishMemory(props_p)
        return num.value


class ArtifactTree(ImageProperty, abc.MutableMapping):
    """Splay tree to map image artifacts. Values defined here
    are intended to be used elseware, and will not be written
    to the encoded image.

    For example::

        # Omit timestamp from PNG file headers.
        with Image(filename='input.png') as img:
            img.artifacts['png:exclude-chunks'] = 'tIME'
            img.save(filename='output.png')

    :param image: an image instance
    :type image: :class:`Image`

    .. note::

       You don't have to use this by yourself.
       Use :attr:`Image.artifacts` property instead.

    .. versionadded:: 0.5.0
    """

    def __init__(self, image):
        if not isinstance(image, Image):
            raise TypeError('expected a wand.image.Image instance, '
                            'not ' + repr(image))
        super(ArtifactTree, self).__init__(image)

    def __getitem__(self, k):
        """
        :param k: Metadata header name string.
        :type k: :class:`basestring`
        :returns: a header value string
        :rtype: :class:`str`

        .. versionadded: 0.5.0
        """
        assertions.assert_string(key=k)
        image = self.image
        v = library.MagickGetImageArtifact(image.wand, binary(k))
        if bool(v) is False:
            try:
                v = library.MagickGetImageProperty(image.wand, binary(k))
                value = v.value
            except KeyError:  # pragma: no cover
                value = ""
        else:
            value = v.value
        return text(value)

    def __setitem__(self, k, v):
        """
        :param k: Metadata header name string.
        :type k: :class:`basestring`
        :param v: Value to assign.
        :type v: :class:`basestring`

        .. versionadded: 0.5.0
        """
        assertions.assert_string(key=k, value=v)
        image = self.image
        r = library.MagickSetImageArtifact(image.wand, binary(k), binary(v))
        if not r:  # pragma: no cover
            image.raise_exception()
        return v

    def __delitem__(self, k):
        """
        :param k: Metadata header name string.
        :type k: :class:`basestring`

        .. versionadded: 0.5.0
        """
        assertions.assert_string(key=k)
        image = self.image
        r = library.MagickDeleteImageArtifact(image.wand, binary(k))
        if not r:  # pragma: no cover
            image.raise_exception()

    def __iter__(self):
        image = self.image
        num = ctypes.c_size_t()
        props_p = library.MagickGetImageArtifacts(image.wand, b'', num)
        props = [text(props_p[i]) for i in xrange(num.value)]
        library.MagickRelinquishMemory(props_p)
        return iter(props)

    def __len__(self):
        image = self.image
        num = ctypes.c_size_t()
        props_p = library.MagickGetImageArtifacts(image.wand, b'', num)
        library.MagickRelinquishMemory(props_p)
        return num.value


class ProfileDict(ImageProperty, abc.MutableMapping):
    """The mapping table of embedded image profiles.

    Use this to get, set, and delete whole profile payloads on an image. Each
    payload is a raw binary string.

    For example::

        with Image(filename='photo.jpg') as img:
            # Extract EXIF
            with open('exif.bin', 'wb') as payload:
                payload.write(img.profiles['exif])
            # Import ICC
            with open('color_profile.icc', 'rb') as payload:
                img.profiles['icc'] = payload.read()
            # Remove XMP
            del imp.profiles['xmp']

    .. seealso::

        `Embedded Image Profiles`__ for a list of supported profiles.

        __ https://imagemagick.org/script/formats.php#embedded

    .. versionadded:: 0.5.1
    """
    def __init__(self, image):
        if not isinstance(image, Image):
            raise TypeError('expected a wand.image.Image instance, '
                            'not ' + repr(image))
        super(ProfileDict, self).__init__(image)

    def __delitem__(self, k):
        assertions.assert_string(key=k)
        num = ctypes.c_size_t(0)
        profile_p = library.MagickRemoveImageProfile(self.image.wand,
                                                     binary(k), num)
        library.MagickRelinquishMemory(profile_p)

    def __getitem__(self, k):
        assertions.assert_string(key=k)
        num = ctypes.c_size_t(0)
        profile_p = library.MagickGetImageProfile(self.image.wand,
                                                  binary(k), num)
        if num.value > 0:
            if PY3:
                return_profile = bytes(profile_p[0:num.value])
            else:
                return_profile = str(bytearray(profile_p[0:num.value]))
            library.MagickRelinquishMemory(profile_p)
        else:
            return_profile = None
        return return_profile

    def __iter__(self):
        num = ctypes.c_size_t(0)
        profiles_p = library.MagickGetImageProfiles(self.image.wand, b'', num)
        profiles = [text(profiles_p[i]) for i in xrange(num.value)]
        library.MagickRelinquishMemory(profiles_p)
        return iter(profiles)

    def __len__(self):
        num = ctypes.c_size_t(0)
        profiles_p = library.MagickGetImageProfiles(self.image.wand, b'', num)
        library.MagickRelinquishMemory(profiles_p)
        return num.value

    def __setitem__(self, k, v):
        assertions.assert_string(key=k)
        if not isinstance(v, binary_type):
            raise TypeError('value must be a binary string, not ' + repr(v))
        r = library.MagickSetImageProfile(self.image.wand,
                                          binary(k), v, len(v))
        if not r:
            self.image.raise_exception()


class ChannelImageDict(ImageProperty, abc.Mapping):
    """The mapping table of separated images of the particular channel
    from the image.

    :param image: an image instance
    :type image: :class:`Image`

    .. note::

       You don't have to use this by yourself.
       Use :attr:`Image.channel_images` property instead.

    .. versionadded:: 0.3.0

    """

    def __iter__(self):
        return iter(CHANNELS)

    def __len__(self):
        return len(CHANNELS)

    def __getitem__(self, channel):
        c = CHANNELS[channel]
        img = self.image.clone()
        if library.MagickSeparateImageChannel:
            succeeded = library.MagickSeparateImageChannel(img.wand, c)
        else:
            succeeded = library.MagickSeparateImage(img.wand, c)
        if not succeeded:
            try:
                img.raise_exception()
            except WandException:
                img.close()
                raise
        return img


class ChannelDepthDict(ImageProperty, abc.Mapping):
    """The mapping table of channels to their depth.

    :param image: an image instance
    :type image: :class:`Image`

    .. note::

       You don't have to use this by yourself.
       Use :attr:`Image.channel_depths` property instead.

    .. versionadded:: 0.3.0

    """

    def __iter__(self):
        return iter(CHANNELS)

    def __len__(self):
        return len(CHANNELS)

    def __getitem__(self, channel):
        c = CHANNELS[channel]
        if library.MagickGetImageChannelDepth:
            depth = library.MagickGetImageChannelDepth(self.image.wand, c)
        else:
            mask = 0
            if c != 0:
                mask = library.MagickSetImageChannelMask(self.image.wand, c)
            depth = library.MagickGetImageDepth(self.image.wand)
            if mask != 0:
                library.MagickSetImageChannelMask(self.image.wand, mask)
        return int(depth)


class HistogramDict(abc.Mapping):
    """Specialized mapping object to represent color histogram.
    Keys are colors, and values are the number of pixels.

    :param image: the image to get its histogram
    :type image: :class:`BaseImage`

    .. versionadded:: 0.3.0

    """

    def __init__(self, image):
        self.size = ctypes.c_size_t()
        self.pixels = library.MagickGetImageHistogram(
            image.wand,
            ctypes.byref(self.size)
        )
        self.counts = None

    def __del__(self):
        if self.pixels:
            self.pixels = library.DestroyPixelWands(self.pixels,
                                                    self.size.value)

    def __len__(self):
        if self.counts is None:
            return self.size.value
        return len(self.counts)

    def __iter__(self):
        if self.counts is None:
            self._build_counts()
        return iter(self.counts)

    def __getitem__(self, color):
        if self.counts is None:
            self._build_counts()
        if isinstance(color, string_type):
            color = Color(color)
        assertions.assert_color(color=color)
        return self.counts[color]

    def _build_counts(self):
        self.counts = {}
        for i in xrange(self.size.value):
            color_count = library.PixelGetColorCount(self.pixels[i])
            color = Color.from_pixelwand(self.pixels[i])
            self.counts[color] = color_count


class ConnectedComponentObject(object):
    """Generic Python wrapper to translate
    :c:type:`CCObjectInfo` structure into a class describing objects found
    within an image. This class is generated by
    :meth:`Image.connected_components()
    <wand.image.BaseImage.connected_components>` method.

    .. versionadded:: 0.5.5
    """
    #: (:class:`numbers.Integral`) Serialized object identifier
    #: starting at `0`.
    _id = None

    #: (:class:`numbers.Integral`) Width of objects minimum
    #: bounding rectangle.
    width = None

    #: (:class:`numbers.Integral`) Height of objects minimum
    #: bounding rectangle.
    height = None

    #: (:class:`numbers.Integral`) X offset of objects minimum
    #: bounding rectangle.
    left = None

    #: (:class:`numbers.Integral`) Y offset of objects minimum
    #: bounding rectangle.
    top = None

    #: (:class:`numbers.Real`) X offset of objects centroid.
    center_x = None

    #: (:class:`numbers.Real`) Y offset of objects centroid.
    center_y = None

    #: (:class:`numbers.Real`) Quantity of pixels that make-up
    #: the objects shape.
    area = None

    #: (:class:`~wand.color.Color`) The average color of the
    #: shape.
    mean_color = None

    def __init__(self, cc_object=None):
        if isinstance(cc_object, CCObjectInfo):
            self.clone_from_cc_object_info(cc_object)

    @property
    def size(self):
        """(:class:`tuple` (:attr:`width`, :attr:`height`))
        Minimum bounding rectangle."""
        return self.width, self.height

    @property
    def offset(self):
        """(:class:`tuple` (:attr:`left`, :attr:`top`))
        Position of objects minimum bounding rectangle."""
        return self.left, self.top

    @property
    def centroid(self):
        """(:class:`tuple` (:attr:`center_x`, :attr:`center_y`))
        Center of object."""
        return self.center_x, self.center_y

    def clone_from_cc_object_info(self, cc_object):
        """Copy data from :class:`~wand.cdefs.structures.CCObjectInfo`."""
        self._id = cc_object._id
        self.width = cc_object.bounding_box.width
        self.height = cc_object.bounding_box.height
        self.left = cc_object.bounding_box.x
        self.top = cc_object.bounding_box.y
        self.center_x = cc_object.centroid.x
        self.center_y = cc_object.centroid.y
        self.area = cc_object.area
        pinfo_size = ctypes.sizeof(PixelInfo)
        raw_buffer = ctypes.create_string_buffer(pinfo_size)
        ctypes.memmove(raw_buffer,
                       ctypes.byref(cc_object.color),
                       pinfo_size)
        self.mean_color = Color(raw=raw_buffer)

    def __repr__(self):
        fmt = ("{name}({_id}: {width}x{height}+{left}+{top} {center_x:.2f},"
               "{center_y:.2f} {area:.0f} {mean_color})")
        return fmt.format(name=self.__class__.__name__, **self.__dict__)


class ClosedImageError(DestroyedResourceError):
    """An error that rises when some code tries access to an already closed
    image.

    """
