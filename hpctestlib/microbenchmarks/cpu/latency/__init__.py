# Copyright 2016-2021 Swiss National Supercomputing Centre (CSCS/ETH Zurich)
# ReFrame Project Developers. See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: BSD-3-Clause

import reframe as rfm
import reframe.utility.sanity as sn
import reframe.utility.typecheck as typ

__all__ = ['CpuLatency']


class CpuLatency(rfm.RegressionTest, pin_prefix=True):
    ''' CPU latency test.

    Derived tests must set the variables ``buffer_size`` and ``num_tasks``.
    The variable ``buffer_sizes`` is a list of the different buffer sizes to
    be used on this latency test. The executable will return the latency in
    ``ns`` for each of the buffer sizes specified in this list.

    This test assumes that the list of buffer sizes is provided in increasing
    order, and this test will automatically extract a performance variable for
    the latency of each buffer. These performance variables are named
    ``latencyL1``, ``latencyL2`` and so on in increasing order.
    '''

    # Required variables
    buffer_sizes = variable(typ.List[str])
    num_tasks = required

    sourcepath = 'latency.cpp'
    build_system = 'SingleSource'
    num_tasks_per_node = 1
    maintainers = ['SK', 'JO']

    @run_before('compile')
    def set_compiler_flags(self):
        self.build_system.cxxflags = ['-O3']

    @run_before('run')
    def set_exc_opts(self):
        '''Set the ``buffer_sizes`` as the executable options.'''
        self.executable_opts = self.buffer_sizes

    @run_before('sanity')
    def set_sanity_patterns(self):
        '''Verify the number of reported latency measurements.'''

        self.sanity_patterns = sn.assert_eq(
            sn.count(sn.findall(r'latency \(ns\)', self.stdout)),
            self.num_tasks*sn.count(self.executable_opts)
        )

    @sn.sanity_function
    def get_latency(self, buffer_size):
        '''Extract the worst latency for a given buffer size.'''

        return sn.max(sn.extractall(
            r'latency \(ns\) for input size %s: (?P<bw>\S+) clocks' %
            buffer_size, self.stdout, 'bw', float
        ))

    @run_before('performance')
    def set_references(self):
        '''Set dummy references to get the perf values in the perf report.

        This will create as many levels as items in ``buffer_sizes``. Derived
        test must override this hook if they wish to use their own reference
        values.
        '''

        self.reference = {
            '*': {
                f'latencyL{i+1}': (None, None, None, 'ns')
                for i, buff in enumerate(self.buffer_sizes)
            }
        }

    @run_before('performance')
    def set_perf_patterns(self):
        '''Set the performance patters to extract all latency levels.

        The levels are named from ``L1`` to ``L{n}``, where ``n`` is the
        length of ``buffer_sizes``.
        '''

        self.perf_patterns = {
            f'latencyL{i+1}': self.get_latency(buff)
            for i, buff in enumerate(self.buffer_sizes)
        }