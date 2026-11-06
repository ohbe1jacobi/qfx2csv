#!/usr/bin/env python

# Standard library imports
import csv
import argparse
from io import BytesIO
from csv import Dialect
from datetime import datetime
from argparse import ArgumentParser

# OFXTools imports
import ofxtools
from ofxtools.Parser import OFXTree
from ofxtools.models import STMTTRN


class CSVConfig(Dialect):
    delimiter = ","
    doublequote = False
    escapechar = None
    lineterminator = "\r\n"
    quotechar = '"'
    quoting = csv.QUOTE_NONE
    skipinitialspace = True
    strict = True


class ArgList:
    """
    Iterate through OFXTools' STMTTRN
    attributes for a list of possible
    values
    """

    # Statically named arguments
    source_file: str = "example.ofx"

    def __init__(self):
        stmt_dummy = STMTTRN(
            trntype="OTHER",
            dtposted=datetime.now(ofxtools.utils.UTC),
            trnamt=0.01,
            fitid="x",
        )
        stmt_dict = vars(stmt_dummy)

        for key in stmt_dict.keys():
            setattr(self, key, False)


def cli_arg_constructor() -> ArgumentParser:
    """
    Dynamically create CLI enabling flags
    """

    arglist = ArgList()
    arg_dict = vars(arglist)

    cmdparser = argparse.ArgumentParser(
        description="Converts OFX and QFX files to CSV format"
    )
    cmdparser.add_argument("source_file", help="OFX or QFX file to convert to CSV")

    for option in arg_dict:
        if not option == "source_file":
            cmdparser.add_argument(
                "--" + option, help="Include this data in the CSV", action="store_true"
            )
    return cmdparser

def fix_encoding_header(fileobj) -> BytesIO:
    """
    Some banks (Notably Itaú Emps) set charset inside file wrongly to specific 
    charset but exports the file in UTF-8, driving nuts to OFXTool Parse object
    """
    raw = fileobj.read()
    try:
        raw.decode("utf-8")
    except UnicodeDecodeError:
        return BytesIO(raw)  # not UTF-8, header's claim (cp1252) may be right
    # Other cases may be inserted here as happens
    if b"CHARSET:1252" in raw:
        raw = raw.replace(b"ENCODING:USASCII", b"ENCODING:UNICODE", 1)
        raw = raw.replace(b"CHARSET:1252", b"CHARSET:NONE", 1)
    return BytesIO(raw)

def to_csv(arglist: ArgList):
    """
    Convert OFX/QFX file to CSV
    """

    # Get the field names we are grabbing
    arg_dict = vars(arglist)
    arg_list = []

    for key in arg_dict:
        if arg_dict[key] is True:
            arg_list.append(key)

    print(arg_list)

    parser = OFXTree()
    with open(arglist.source_file, "rb") as fileobj:
        parser.parse(fix_encoding_header(fileobj))
        ofx = parser.convert()

        statements = ofx.statements
        transactions = statements[0].transactions

        with open(arglist.source_file + ".csv", "w", newline="") as csvfile:
            csvconfig = CSVConfig()
            csvwriter = csv.writer(csvfile, dialect=csvconfig)
            csvwriter.writerow(arg_list)

            for trx in transactions:
                row = []
                for field in arg_list:
                    row.append(str(getattr(trx, field)))
                csvwriter.writerow(row)


def main():
    arglist = ArgList()
    argparser = cli_arg_constructor()

    cmdargs = vars(argparser.parse_args())
    for key in cmdargs:
        setattr(arglist, key, cmdargs[key])

    to_csv(arglist)


if __name__ == "__main__":
    main()
