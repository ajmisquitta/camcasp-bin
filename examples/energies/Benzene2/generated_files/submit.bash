#!/bin/bash
queue="$QUEUE"
[[ -z $queue ]] && queue="small"
while [[ $# -gt 0 ]]; do
  case $1 in
    -q )
    queue=$2
    shift;;
  esac
  shift
done
cd /scratch2/am592/examples/energies/benzene2/benzene2_1
if [[ $queue = "bg" ]]; then
  bash ./benzene2_1.bash &
else
  qsub -q $queue benzene2_1.bash
fi
