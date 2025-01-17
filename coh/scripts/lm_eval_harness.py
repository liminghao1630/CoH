# This script runs lm_eval_harness evaluations against a served language model.
# Typically, you need to run a language model server first, e.g.:
#    python -m coh.models.gptj.gptj_serve ...

import dataclasses
import pprint
from functools import partial
import os
from tqdm import tqdm, trange
import numpy as np
import coh.utils as utils

from flax.traverse_util import flatten_dict
from lm_eval import evaluator, tasks
from lm_eval.base import LM

from coh.serving import LMClient


FLAGS, FLAGS_DEF = utils.define_flags_with_default(
    tasks='wsc,piqa,winogrande,openbookqa,logiqa',
    shots=0,
    lm_client=LMClient.get_default_config(),
    logger=utils.WandBLogger.get_default_config(),
)


class LMEvalHarnessInterface(LM):

    def __init__(self, lm_client):
        self.lm_client = lm_client

    def greedy_until(self, inputs):
        prefix, until = zip(*inputs)
        return self.lm_client.greedy_until(prefix, until)

    def loglikelihood_rolling(self, inputs):
        loglikelihoods, is_greedys = self.lm_client.loglikelihood_rolling(inputs)
        return list(zip(loglikelihoods, is_greedys))

    def loglikelihood(self, inputs):
        prefix, text = zip(*inputs)
        loglikelihoods, is_greedys = self.lm_client.loglikelihood(prefix, text)
        return list(zip(loglikelihoods, is_greedys))


def main(argv):
    logger = utils.WandBLogger(
        config=FLAGS.logger, variant=utils.get_user_flags(FLAGS, FLAGS_DEF)
    )
    model = LMEvalHarnessInterface(LMClient(FLAGS.lm_client))
    task_list = FLAGS.tasks.split(',')
    results = evaluator.evaluate(
        model, tasks.get_task_dict(task_list), False, FLAGS.shots, None
    )
    logger.log(flatten_dict(results['results'], sep='/'))
    pprint.pprint(results)


if __name__ == "__main__":
    utils.run(main)
