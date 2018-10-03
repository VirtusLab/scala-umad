#!/usr/bin/python3

import argparse
import os
import re
import subprocess
import sys
import tempfile
import time

from glob import glob

parser = argparse.ArgumentParser()
parser.add_argument('-s', '--scala', dest='scala', help='Path to the Scala build dir')
parser.add_argument('-d', '--debugPort', dest='debugPort', help='Port on which remote debugger can be attached')
parser.add_argument('-c', '--corpus', dest='corpus', default="scala-library", help='Project to compile')
parser.add_argument('-f', '--jfr-file', dest='jfrFile', 
    help='Enable Java Flight Recorder and write the recording to this file (requires Oracle JVM)')
parser.add_argument('-n', '--repeat', dest='repeat', type=int, default=1, help='Repeat the compilation n times')
parser.add_argument('-p', '--config', dest='config', default=[], type=str, nargs='+',
    help='Config overrides (key=value pairs)')
parser.add_argument('additionalOptions', type=str, nargs="*")

options = parser.parse_args()

def findFiles(path, regex):
    rx = re.compile(regex)
    files = []
    for path, dnames, fnames in os.walk(path):
        files.extend([os.path.join(path, file) for file in fnames if rx.search(file)])
    return files


corpus = os.path.join("corpus", options.corpus)

sources = findFiles(os.path.join(corpus, "src"), r'\.(scala$|java$)')

if len(sources) < 1:
    print("No sources found in corpus:", corpus)
    sys.exit(1)

jars = findFiles(os.path.join(corpus, "lib"), r'\.jar')

scalaJars = findFiles(os.path.join(options.scala, "lib"), r'\.jar')

scalacOptions = ["-encoding", "UTF-8", "-target:jvm-1.8", "-feature", "-unchecked", "-nowarn",
                 "-Xlog-reflective-calls", "-Xlint", "-opt:l:none", "-J-XX:MaxInlineSize=0", "-J-Xmx6g"]

debugOptions = []
if options.debugPort:
    debugOptions = [
        "-J-agentlib:jdwp=transport=dt_socket,server=n,address=localhost:{},suspend=y".format(options.debugPort)]
        
outputBase = tempfile.mkdtemp()
scalaOutput = os.path.join(outputBase, "scala")
os.mkdir(scalaOutput)
jfrOutput = os.path.join(outputBase, "jfr")
if options.jfrFile:
    os.mkdir(jfrOutput)        
        
def createJfrOptions(index):
    if not options.jfrFile:
        return []
    else:
        jfrOptions = ["-XX:+UnlockCommercialFeatures", "-XX:+FlightRecorder", 
        "-XX:+UnlockDiagnosticVMOptions", "-XX:+DebugNonSafepoints"]
        filename = os.path.join(jfrOutput, "{0:03d}.jfr".format(index))
        parameters = "-XX:StartFlightRecording=settings=profile,dumponexit=true,filename={}".format(filename)
        jfrOptions.append(parameters)
        return map(lambda v: "-J" + v, jfrOptions)

classpathSeparator = ";" if os.name == 'nt' else ":"

def call_compiler(scalaLocation, output, additionalScalacOptions, index):
    configOverrides = map(lambda v: "-J-D" + v, options.config)
    timeBefore = time.time()
    args = ([ os.path.join(scalaLocation, "bin", "scalac"), "-cp", classpathSeparator.join(scalaJars + jars), "-d", output ] +
        list(configOverrides) +
        scalacOptions +
        sources +
        debugOptions +
        list(createJfrOptions(index)) +
        additionalScalacOptions)
    subprocess.run(args)
    return time.time() - timeBefore

for i in range(0, options.repeat):
    compilation_time = call_compiler(options.scala, scalaOutput, options.additionalOptions, i)
    print("Compilation done in:", compilation_time, "s")

if options.jfrFile:
    subprocess.run(["java", "oracle.jrockit.jfr.tools.ConCatRepository", jfrOutput, "-o", options.jfrFile])

