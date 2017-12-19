import lldb
import lldb.formatters.Logger

def format_thread(target, tid):
    thread = target.GetProcess().GetThreadByID(tid)
    if not thread:
        return "(unknown thread ID %s)" % hex(tid)
    return "#%d (%s)" % (thread.GetIndexID(), hex(tid))

def pthread_mutex_t_SummaryProvider(valobj, dict):
    # layout:
    # (regsize) signature (not in opaque)
    # 4b   lock
    # 4b   opts
    # 2b   prioceiling
    # 2b   priority
    # (pad to reg-size align)
    # 4bx2 locked tid
    # 4bx2 sequence id
    # 4bx2 overflow tid/sid for misaligned locks

    logger = lldb.formatters.Logger.Logger()

    target = valobj.GetTarget()

    longsize = target.FindFirstType("long").GetByteSize()

    sig = valobj.GetChildAtIndex(0)
    opaque = valobj.GetChildAtIndex(1)
    data = opaque.GetData()

    addr = valobj.AddressOf().GetValueAsUnsigned()

    offset = 0

    err = lldb.SBError()

    lock = data.GetUnsignedInt32(err, offset)
    offset += 4
    opts = data.GetUnsignedInt32(err, offset)
    offset += 4
    prioceiling = data.GetUnsignedInt16(err, offset)
    offset += 2
    priority = data.GetUnsignedInt16(err, offset)
    offset += 2
    if longsize == 8:
        offset += 4

    alignedAddr = (addr + 0x7) & ~0x7
    if alignedAddr != addr:
        offset += (alignedAddr - addr)

    tid = data.GetUnsignedInt64(err, offset)
    offset += 8
    seq = data.GetUnsignedInt64(err, offset)
    offset += 8

    if tid == 0:
        return '<free mutex>'
    else:
        return 'held by thread: %s' % format_thread(target, tid)

def __lldb_init_module(debugger, dict):
    debugger.HandleCommand(
        'type summary add -F libpthread.pthread_mutex_t_SummaryProvider pthread_mutex_t -w pthread')
    debugger.HandleCommand(
        'type category enable pthread')
