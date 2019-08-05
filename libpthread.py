import lldb
import lldb.formatters.Logger

def align(x, a):
    return (((x)+(a)-1)&~((a)-1))

def format_thread(target, tid):
    thread = target.GetProcess().GetThreadByID(tid)
    if not thread:
        return "(unknown thread ID %d)" % tid
    return "thread #%d (id %d)" % (thread.GetIndexID(), tid)

def pthread_t_SummaryProvider(valobj, dict):
    # layout:
    # (regsize) signature (not in opaque)
    # (regsize) cleanup_stack* (not in opaque)
    # 4b flags bitfield
    # 4b lock
    # 4b flags2 bitfield
    # (pad to reg-size align)
    # regx4 (various pointers)
    # 4bx4 (various ints)
    # reg joiner*
    # 8b sched_param
    # regx2 queue
    # char[64] name
    # regx5 (various stack stuff)
    # (pad to 8-byte align)
    # 8b thread_id
    # (pad to 16-byte align)
    # reg[N] tsd pointer array
    target = valobj.GetTarget()
    longsize = target.FindFirstType("long").GetByteSize()

    opaque = valobj.GetChildAtIndex(2)

    data = opaque.GetData()

    offset = 0

    err = lldb.SBError()

    offset += 4 * 3
    offset = align(offset, longsize)
    offset += longsize * 4
    offset += 4 * 4
    offset += longsize
    offset += 8
    offset += longsize * 2
    offset += 64
    offset += longsize * 5
    offset = align(offset, 8)
    tid = data.GetUnsignedInt64(err, offset)
    offset += 8
    offset = align(offset, 16)
    return format_thread(target, tid)

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

    alignedAddr = align(addr, 8)
    if alignedAddr != addr:
        offset += (alignedAddr - addr)

    tid = data.GetUnsignedInt64(err, offset)
    offset += 8
    seq = data.GetUnsignedInt64(err, offset)
    offset += 8

    if tid == 0:
        return '<free mutex>'
    else:
        return 'held by: %s' % format_thread(target, tid)

def __lldb_init_module(debugger, dict):
    debugger.HandleCommand(
        'type summary add -F libpthread.pthread_t_SummaryProvider pthread_t -w pthread')
    debugger.HandleCommand(
        'type summary add -F libpthread.pthread_mutex_t_SummaryProvider pthread_mutex_t -w pthread')
    debugger.HandleCommand(
        'type category enable pthread')
