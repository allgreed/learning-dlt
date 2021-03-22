import sys

def acquire_user_initials_or_exit():
    try:
        username = sys.argv[1]
    except IndexError:
        print("Provide user initials, would you kindly?",file=sys.stderr)
        exit(1)

    if len(username) != 2:
        print("AAA!!!!! must be exactly 2 characters!",file=sys.stderr)
        exit(1)
    if not (username.isascii() and username.isprintable()):
        print("Nice try...",file=sys.stderr)
        exit(2)

    print(f"Hello, {username}")
    return username
