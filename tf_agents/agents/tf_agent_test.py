# coding=utf-8
# Copyright 2018 The TF-Agents Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for agents.tf_agent."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import copy
import numpy as np
import tensorflow as tf  # pylint: disable=g-explicit-tensorflow-version-import

from tf_agents.agents import tf_agent
from tf_agents.policies import tf_policy
from tf_agents.specs import array_spec
from tf_agents.specs import tensor_spec
from tf_agents.trajectories import time_step as ts
from tf_agents.trajectories import trajectory
from tf_agents.utils import test_utils


class LossInfoTest(tf.test.TestCase):

  def testBaseLossInfo(self):
    loss_info = tf_agent.LossInfo(0.0, ())
    self.assertEqual(loss_info.loss, 0.0)
    self.assertIsInstance(loss_info, tf_agent.LossInfo)


class MyAgent(tf_agent.TFAgent):

  def __init__(self):
    obs_spec = {'obs': tf.TensorSpec([], tf.float32)}
    time_step_spec = ts.time_step_spec(obs_spec)
    action_spec = ()
    train_argspec = {'extra': tf.TensorSpec(dtype=tf.float32, shape=[3, 4])}
    policy = tf_policy.Base(time_step_spec, action_spec)
    super(MyAgent, self).__init__(
        time_step_spec=time_step_spec,
        action_spec=action_spec,
        policy=policy,
        collect_policy=policy,
        train_sequence_length=None,
        train_argspec=train_argspec)

  def _train(self, experience, weights=None, extra=None):
    return tf_agent.LossInfo(loss=(), extra=(experience, extra))


class TFAgentTest(tf.test.TestCase):

  def testTrainArgspec(self):
    agent = MyAgent()
    extra = tf.ones(shape=[3, 4], dtype=tf.float32)
    experience = tf.nest.map_structure(
        lambda x: x[tf.newaxis, ...],
        trajectory.from_episode(
            observation={'obs': tf.constant([1.0])},
            action=(),
            policy_info=(),
            reward=tf.constant([1.0])))
    loss_info = agent.train(experience, extra=extra)
    tf.nest.map_structure(
        self.assertAllEqual, (experience, extra), loss_info.extra)
    extra_newdim = tf.ones(shape=[2, 3, 4], dtype=tf.float32)
    loss_info_newdim = agent.train(experience, extra=extra_newdim)
    self.assertAllEqual(loss_info_newdim.extra[1], extra_newdim)
    with self.assertRaisesRegex(
        ValueError, 'Inconsistent dtypes or shapes between'):
      agent.train(experience, extra=tf.ones(shape=[3, 5], dtype=tf.float32))
    with self.assertRaisesRegex(
        ValueError, 'Inconsistent dtypes or shapes between'):
      agent.train(experience, extra=tf.ones(shape=[3, 4], dtype=tf.int32))

  def testTrainIgnoresExtraFields(self):
    agent = MyAgent()
    extra = tf.ones(shape=[3, 4], dtype=tf.float32)
    experience = tf.nest.map_structure(
        lambda x: x[tf.newaxis, ...],
        trajectory.from_episode(
            observation={
                'obs': tf.constant([1.0]), 'ignored': tf.constant([2.0])},
            action=(),
            policy_info=(),
            reward=tf.constant([1.0])))
    loss_info = agent.train(experience, extra=extra)
    reduced_experience = experience._replace(
        observation=copy.copy(experience.observation))
    del reduced_experience.observation['ignored']
    tf.nest.map_structure(
        self.assertAllEqual, (reduced_experience, extra), loss_info.extra)


class AgentSpecTest(test_utils.TestCase):

  def testErrorOnWrongTimeStepSpecWhenCreatingAgent(self):
    wrong_time_step_spec = ts.time_step_spec(
        array_spec.ArraySpec([2], np.float32))
    action_spec = tensor_spec.BoundedTensorSpec([1], tf.float32, -1, 1)
    with self.assertRaisesRegex(
        TypeError, 'time_step_spec has to contain TypeSpec'):
      tf_agent.TFAgent(wrong_time_step_spec, action_spec, None, None, None)

  def testErrorOnWrongActionSpecWhenCreatingAgent(self):
    time_step_spec = ts.time_step_spec(tensor_spec.TensorSpec([2], tf.float32))
    wrong_action_spec = array_spec.BoundedArraySpec([1], np.float32, -1, 1)
    with self.assertRaisesRegex(
        TypeError, 'action_spec has to contain BoundedTensorSpec'):
      tf_agent.TFAgent(time_step_spec, wrong_action_spec, None, None, None)


if __name__ == '__main__':
  test_utils.main()
