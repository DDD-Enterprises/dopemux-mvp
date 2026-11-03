"""Private staging entrypoint. No enrollment or executable dispatch interface."""


def status():
    return {
        'state': 'DISABLED',
        'dispatch': 'HELD',
        'scope': 'PRIVATE_STAGING_ONLY',
        'activation': 'NOT_AUTHORIZED',
    }


def dispatch(*args, **kwargs):
    """Accept no activation authority, including ambient configuration."""
    return {'status': 'HELD', 'reason': 'DISABLED', 'fixture': False}


def main(argv=None):
    import sys
    args = list(sys.argv[1:] if argv is None else argv)
    if args in ([], ['status']):
        print('DISABLED; dispatch HELD; PRIVATE_STAGING_ONLY')
        return 0
    if args in (['--help'], ['-h'], ['help']):
        print('Usage: disabled_entrypoint [status|--help]\n'
              'Private staging only. DISABLED; dispatch HELD. No activation command.')
        return 0
    print('HELD: DISABLED. No activation or dispatch command is available.')
    return 2


if __name__ == '__main__':
    raise SystemExit(main())
