__author__ = 'github.com/wardsimon'
__version__ = ''

from copy import deepcopy
from datetime import datetime
from typing import NoReturn, Union
import re
import sys

import semver
import json


def createVersion(release_notes: dict, release_type: str) -> str:
    """
    Get the version number and bump by release type.

    :param release_notes: Loaded Release.json
    :param release_type: 'major', 'minor', 'patch', 'prerelease', 'build'
    :return: Bumped release version
    """

    ver = semver.parse_version_info(release_notes['version'])
    if release_type == 'major':
        ver = ver.bump_major()
    elif release_type == 'minor':
        ver = ver.bump_minor()
    elif release_type == 'patch':
        ver = ver.bump_patch()
    elif release_type == 'prerelease':
        ver = ver.bump_prerelease()
    elif release_type == 'build':
        ver = ver.bump_build()
    else:
        raise KeyError

    return str(ver)


def readRelease(release_file: str) -> dict:
    try:
        with open(release_file) as json_file:
            release_info = json.load(json_file)
    except FileNotFoundError:
        print('File {} can not be found'.format(release_file))
        raise FileNotFoundError
    return release_info


def parseMessage(message: str) -> dict:
    out = {
        "name": None,
        "version": None,
        "date": None,
        "author": None,
        "url": None,
        "comments": None,
        "changes": []
    }

    if '\n' in message:
        # we can split
        message_list = message.split('\n')
        for message_str in message_list:
            if '::' in message_str:
                ident, info = message_str.split('::', 1)
                if ident == 'changes':
                    idx = message_list.index(message_str)
                    for change in message_list[idx + 1::]:
                        if '::' in change:
                            break
                        out[ident].append(change)
                if ident in out.keys():
                    out[ident] = info
                else:
                    print('Unknown option: {}'.format(ident))
    else:
        if '::' in message:
            ident, info = message.split('::')
            if ident in out.keys():
                out[ident] = info
            else:
                print('Unknown option: {}'.format(ident))
    return out


def updateRelease(current_dict: dict, updates: dict) -> dict:
    out_dict = deepcopy(current_dict)
    for key in updates.keys():
        if key in current_release.keys():
            if updates[key] is not None:
                if isinstance(updates[key], str):
                    if updates[key] == '':
                        continue
                elif isinstance(updates[key], list):
                    if len(updates[key]) == 0:
                        continue
                out_dict[key] = updates[key]
        else:
            print('Unknown Option: {}'.format(key))
    return out_dict


def saveRelease(out_file: str, release: dict) -> NoReturn:
    with open(out_file, 'w') as file_writer:
        file_writer.write(json.dumps(release))


def parseHeader(header: str) -> Union[str, None]:
    options = re.findall('\[(.+?)\]', header)
    result = None
    for option in options:
        if 'release' in option:
            if option == 'prerelease':
                return option
            else:
                try:
                    _, result = option.split(' ')
                    return result
                except ValueError:
                    # In this case we just have release
                    return 'patch'
        elif 'build' in option:
            return 'build'
    return result


if __name__ == '__main__':

    message_full = sys.argv[1]
    try:
        header, message = message_full.split('\n\n', 1)
    except ValueError:
        # We do not have a message body
        sys.stdout.write('')
        sys.exit(0)

    current_release = readRelease('Release.json')
    release_changes = parseMessage(message)
    # print(current_release)
    # print(release_changes)

    # for header in test_header_list:
    release_type = parseHeader(header)
    new_release = updateRelease(current_release, release_changes)
    # print(release_type)
    if release_type is not None:
        new_release['version'] = createVersion(new_release, release_type)
        new_release['date'] = datetime.now().strftime('%d %b %Y')
        sys.stdout.write('v{}'.format(new_release['version']))
        saveRelease('Release.json', new_release)
    else:
        # We are not performing a release
        sys.stdout.write('')
        # print(json.dumps(new_release))
