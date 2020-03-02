#!/usr/bin/env python


# INFO
#
# This script was used to gather information on the contributions of our group
# to the FHIaims source code.
# If you need to gather such information, for example for project documentation
# or funding stuff, you might be able to use this script.
#
# Ask Christoph Scheurer for details on what this information was for
# and
# Ask Christoph Schober for details on how this script works (and why it looks
# so complicated...)

import subprocess
import os
import re

comm = "september2"

s = "2000-01-01"
e = "3000-01-01"
full = [s, e]
#               author              since, until
author_list = {"Christoph Schober": full,
               "Daniel Berger": [s, "2014-12-31"],
               "Georg Michelitsch": full,
               "Harald Oberhofer": full,
               "Joerg Meyer": [s, "2013-12-31"],
               "Lukas": full,
               "Lydia Nemec": ["2015-01-01", e],
               "lnemec": ["2015-01-01", e],
               "Matthias Kick": full,
               "Reinhard Maurer": [s, "2014-12-31"],
               "Sinstein": full,
               "Stefan Ringe": full,
               "berger": [s, "2014-12-31"],
               "Ran Jia": [s, "2013-12-01"]}


filecmd = 'git log --no-merges --author="{name}" --stat=$COLUMNS \
--pretty=format:"" --since={since} --until={until} | sort -u'

filedict = {}
for author, times in author_list.items():
    t = subprocess.check_output(filecmd.format(name=author, since=times[0],
                                               until=times[1]), shell=True)
    tt = [x.strip() for x in t.split('\n') if x != '']
    tt2 = []
    for l in tt:
        if "|" in l and "=>" not in l:
            tt2.append(l)
    ttt = [x.split("|") for x in tt2]
    actual_files = {}
    for name, stat in ttt[:-1]:
        match = re.search("\s+0\Z", stat)
        if not match:
            actual_files[name.strip()] = stat

    for file in actual_files.keys():
        try:
            filedict[file].append(author)
        except KeyError:
            filedict[file] = [author]

filesha256sum = {}
for filen in filedict.keys():
    try:
        h = subprocess.check_output("sha256sum {}".format(filen), shell=True)
        filesha256sum[h.split()[0]] = filen
    except subprocess.CalledProcessError:
        print("Did not find file {0}, ignoring".format(filen))
    # finally:
        # print("Iteration of sha256 done")
        # time.sleep(5)


# to check only valid git files in generated dict
full_hashs = subprocess.check_output("find . -type f -print0 -o -type d -name \
                                     '.git' -prune | xargs -0 -n 1 sha256sum | \
                                     sed 's~  \./~  ~'", shell=True)
full_hashs = full_hashs.split("\n")
full_hashs2 = [x.split() for x in full_hashs[:-1]]
full_dict = {}
for hash, file in full_hashs2:
    full_dict[hash] = file

assert filesha256sum.viewitems() <= full_dict.viewitems(), "Invalid files in \
list, check"


still_valid = {}
for hash, file in filesha256sum.items():
    namelist = filedict[file]
    alist = subprocess.check_output('git blame --line-porcelain {} | grep \
                                    "author " | sort -u'.format(file),
                                    shell=True)
    for name in namelist:
        if name in alist:
            try:
                still_valid[file].append(name)
            except KeyError:
                still_valid[file] = [name]

# write out
cwd = os.getcwd()
os.mkdir(comm)
try:
    os.chdir(comm)
    with open(comm+".filelist", "w") as f:
        for i in full_hashs:
            f.write(i)
            f.write("\n")

    with open(comm+".ourfiles", "w") as f:
        for key, value in filesha256sum.items():
            f.write(value)
            f.write("\n")

    with open(comm+".ourfiles_and_names", "w") as f:
        for key, value in filesha256sum.items():
            namelist = filedict[value]
            names = ", ".join(x for x in namelist)
            f.write("{0: <60} {1}".format(value, names))
            f.write("\n")

    # subprocess.call("git shortlog > {0}.shortlog".format(comm), shell=True)
finally:
    os.chdir(cwd)
