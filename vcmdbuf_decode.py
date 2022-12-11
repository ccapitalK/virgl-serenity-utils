#!/usr/bin/python

# Decode a virgl command buffer. Expects the raw binary data from the intercepted command buffer, passed either as a file on the command line or from stdin.

import pprint, struct
import sys

opcodes = [
    ("NOP", None, None),
    ("CREATE_OBJECT", None, None),
    ("BIND_OBJECT", None, None),
    ("DESTROY_OBJECT", None, None),
    ("SET_VIEWPORT_STATE", '<Iffffff', ('start_slot', 'scale_x', 'scale_y', 'scale_z', 'translate_x', 'translate_y', 'translate_z')),
    ("SET_FRAMEBUFFER_STATE", '<III', ('nr_cbufs', 'zsurf_handle', 'surf_handle')),
    ("SET_VERTEX_BUFFERS", None, None),
    ("CLEAR", '<IffffdI', ('buffers', 'red', 'green', 'blue', 'alpha', 'depth', 'stencil')),
    ("DRAW_VBO", '<IIIIIIIIIIII', ("start", "count", "mode", "indexed", "instance_count", "index_bias", "start_instance", "primitive_restart", "restart_index", "min_index", "max_index", "cso")),
    ("RESOURCE_INLINE_WRITE", None, None),
    ("SET_SAMPLER_VIEWS", '<II', ('shader_type', 'start_slot')),
    ("SET_INDEX_BUFFER", None, None),
    ("SET_CONSTANT_BUFFER", None, None),
    ("SET_STENCIL_REF", None, None),
    ("SET_BLEND_COLOR", '<ffff', ('red', 'green', 'blue', 'alpha')),
    ("SET_SCISSOR_STATE", None, None),
    ("BLIT", None, None),
    ("RESOURCE_COPY_REGION", None, None),
    ("BIND_SAMPLER_STATES", None, None),
    ("BEGIN_QUERY", None, None),
    ("END_QUERY", None, None),
    ("GET_QUERY_RESULT", None, None),
    ("SET_POLYGON_STIPPLE", '<IIIIIIIIIIIIIIIIIIIIIIIIIIIIIIII', None),
    ("SET_CLIP_STATE", None, None),
    ("SET_SAMPLE_MASK", None, None),
    ("SET_STREAMOUT_TARGETS", None, None),
    ("SET_RENDER_CONDITION", None, None),
    ("SET_UNIFORM_BUFFER", None, None),
    ("SET_SUB_CTX", '<I', ('sub_ctx_id',)),
    ("CREATE_SUB_CTX", '<I', ('sub_ctx_id',)),
    ("DESTROY_SUB_CTX", '<I', ('sub_ctx_id',)),
    ("BIND_SHADER", '<II', ('handle', 'type')),
    ("SET_TESS_STATE", '<ffffff', None),
    ("SET_MIN_SAMPLES", '<I', ('min_samples',)),
    ("SET_SHADER_BUFFERS", None, None),
    ("SET_SHADER_IMAGES", None, None),
    ("MEMORY_BARRIER", None, None),
    ("LAUNCH_GRID", None, None),
    ("SET_FRAMEBUFFER_STATE_NO_ATTACH", '<II', ('(height << 16 | width)', '(samples << 16 | layers)')),
    ("TEXTURE_BARRIER", None, None),
    ("SET_ATOMIC_BUFFERS", None, None),
    ("SET_DEBUG_FLAGS", None, None),
    ("GET_QUERY_RESULT_QBO", None, None),
    ("TRANSFER3D", '<iiiIIiiiiiiIi', ('res_handle', 'level', 'usage', 'stride', 'layer_stride', 'x', 'y', 'z', 'width', 'height', 'depth', 'data_offset', 'direction')),
    ("END_TRANSFERS", None, None),
    ("COPY_TRANSFER3D", None, None),
    ("SET_TWEAKS", '<II', ('id', 'value')),
    ("CLEAR_TEXTURE", None, None),
    ("PIPE_RESOURCE_CREATE", None, None),
    ("PIPE_RESOURCE_SET_TYPE", None, None),
    ("GET_MEMORY_INFO", None, None),
    ("SEND_STRING_MARKER", None, None)
]

if len(sys.argv) > 1:
    filename = sys.argv[1]
else:
    filename = "/dev/stdin"

with open(filename, 'rb') as f:
    data = f.read()

cmd_struct = struct.Struct('<BBH')

pos = 0
while pos < len(data):
    (command_opc, mid, length) = cmd_struct.unpack(data[pos:pos+4])
    (opc, fmt, fields) = opcodes[command_opc] if command_opc < len(opcodes) else ('UNKNOWN', None, None)
    cmd_len = 4 * (length + 1)
    cmd_args = data[pos+4:pos+cmd_len]
    if opc == 'SET_CONSTANT_BUFFER':
        fmt = '<II' + ((length - 2) * 'f')
        fields = ['shader_type', 'index (unused)'] + ['val_{}'.format(i) for i in range(length-2)]
    elif opc == 'SET_VERTEX_BUFFERS':
        fmt = '<' + (length * 'I')
        fields = ['{}_{}'.format(field, i) for i in range(length//3) for field in ('stride', 'offset', 'handle')]
    elif opc == 'SET_ATOMIC_BUFFERS':
        fmt = '<' + (length * 'I')
        fields = ['start_slot'] + ['{}_{}'.format(field, i) for i in range((length-1)//3) for field in ('offset', 'buf_len', 'handle')]
    elif opc == 'CREATE_OBJECT':
        if mid == 1: #VIRGL_OBJECT_BLEND
            opc += '_BLEND'
            fmt = '<' + 11 * 'I'
        elif mid == 2: #VIRGL_OBJECT_RASTERIZER
            opc += '_RASTERIZER'
        elif mid == 3: #VIRGL_OBJECT_DSA
            opc += '_DSA'
        elif mid == 4: #VIRGL_OBJECT_SHADER
            opc += '_SHADER'
        elif mid == 5: #VIRGL_OBJECT_VERTEX_ELEMENTS
            opc += '_VERTEX_ELEMENTS'
            fmt = '<' + (length * 'I')
            assert((length-1)%4 == 0)
            fields = ['handle'] + ['{}_{}'.format(field, i) for i in range((length-1)//4) for field in ('src_offset', 'instance_divisor', 'vertex_buffer_index', 'src_format')]
        elif mid == 8: #VIRGL_OBJECT_SURFACE
            opc += '_SURFACE'
            fmt = '<IIIII'
            fields = ('handle', 'res_handle', 'format', 'first_element/texture_level', 'last_element/texture_layers')
    elif opc == 'BIND_OBJECT':
        fmt = '<I'
        fields = ('handle',)
        # if mid == 4: #VIRGL_OBJECT_SHADER
        #     pass
    if fmt is not None:
        cmd_args = struct.Struct(fmt).unpack(cmd_args)
        if fields is not None:
            assert(len(fields) == len(cmd_args))
            cmd_args = ''.join(["\n\t{}: {}".format(name, val) for (name, val) in zip(fields, cmd_args)])
    print(opc, (command_opc, mid, length), cmd_args)
    pos += cmd_len

assert(pos == len(data))
