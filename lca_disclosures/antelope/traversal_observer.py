"""
 mainly derived from traversal results.

Every distinct fragment.reference_entity (including distinct None reference flows) should be a column in Af .
By extension, every FragmentFlow that terminates in a fragment should be an entry in Af.  Every FragmentFlow that
terminates in a bg should be an Ad entry, and every null termination should be a cutoff (note that emissions are
currently modeled as foreground-terminated flows with no children, but after ContextRefactor they will be terminated
to compartments;; until that time, only unobserved_exchanges will be included in emissions)

When a flow terminates in a subfragment, the treatment is different for descend=True and descend=False.

In the former case, the subfragment's flows will be duplicated for every instance of the subfragment.  Thus, to ensure
uniqueness, the fg node's "name" should be the fragment's external ref SUFFIXED BY its sequential FFID.  This should
be true for every fragment flow whose top() is not the reference fragment.  For descended-into fragments, their IO
flows will be forwarded out and will appear to emanate from the parent fragment, as distinct fg flows.

In the non-descend case, the subfragment will need to be replicated explicitly in the disclosure-- add it to the
foreground and enqueue the term's subfragments (already cached) to be traversed later.  Any cutoff children of the
parent fragment will thus have emanated from the subfragment and should be discarded.  On the other hand, any non-
cutoff children (i.e. child fragments that have stuff going on) need to be *subtracted* from the cutoff flows, as they
will get fed back in during the traversal) and added equally-and-oppositely as new fg flows to continue following.

Still TODO: figure out how to log these things.  An OFF should be created upon processing the FragmentFlow... when we
get an ff, say we're in a subfragment- we know the most recent parent from the _parents list-- which starts out None,
for the overall reference flow.   So if the end of the _parents list is not None, we are in a subfragment, in which
case the fragment name should be uniquified.-- should be the parent FF's FFID-- so an OFF also needs to know its own
FFID- which is just its position in the sequence of encountered FFIDs.  In fact, that duple - parent, index- SHOULD BE
the unique key-- no, has to be the full tuple of all parents up to None-- but fine, that's the key- and retrieving the
key should get us the OFF, which tells us the fragment entity and the FFID; and trimming the last entry from the key
gives us the key to the most recent parent, which gives us the context we need to determine descent.

Then the only reverse mapping we need is from ff to key, so that given a fragmentflow from the sequence we can retrieve
its OFF without knowing its FFID.
"""


from collections import deque
from .observer import Observer, ObservedFlow, RX


class EmptyFragQueue(Exception):
    pass


class DescentCollision(Exception):
    pass


'''
class ProxyParent(object):
    """
    This is apparently unnecessary- given the bugfixes to handle _descend and _defer
    """
    def __init__(self, off):
        self.fragment = off.term.term_node
        self.term = off.term
'''


class ObservedExchange(ObservedFlow):
    def __init__(self, exch, parent):
        self._exch = exch
        self._key = tuple(parent.key + exch.lkey)
        self.observe(parent)

    @property
    def key(self):
        return self._key

    @property
    def value(self):
        return self._exch.value

    @property
    def flow(self):
        return self._exch.flow

    @property
    def direction(self):
        return self._exch.direction

    @property
    def locale(self):
        try:
            return self._exch.process['SpatialScope']
        except KeyError:
            return ''

    @property
    def context(self):
        return self._exch.termination

    @property
    def context(self):
        return self._exch.termination


class ObservedFragmentFlow(ObservedFlow):
    def __init__(self, ff, key):
        """

        :param ff: the fragmentflow from the traversal
        :param key: the fg key for the fragment
        """
        self.ff = ff
        self._key = key

    @property
    def key(self):
        return self._key

    @property
    def ffid(self):
        return self.key[-1]

    @property
    def value(self):
        if self.parent is RX or self.fragment.is_reference:
            return self.magnitude
        return self.ff.node_weight / self.parent.magnitude

    @property
    def magnitude(self):
        if self.parent is RX or self.fragment.is_reference:
            return self.ff.magnitude
        return self.ff.node_weight

    @property
    def fragment(self):
        return self.ff.fragment

    @property
    def flow(self):
        return self.ff.fragment.flow

    @property
    def direction(self):
        return self.ff.fragment.direction

    @property
    def locale(self):
        try:
            return self.ff.term.term_node['SpatialScope']
        except KeyError:
            return ''

    @property
    def external_ref(self):
        return self.fragment.external_ref

    @property
    def term(self):
        return self.ff.term

    def observe_bg_flow(self):
        bg = ObservedBgFlow(self.ff, self.ffid)
        bg.observe(self.parent)
        return bg

    def observe_em_flow(self):
        em = ObservedEmFlow(self.ff, self.ffid)
        em.observe(self.parent)
        return em

    def __repr__(self):
        return str(self)

    def __str__(self):
        return 'ObservedFragmentFlow(Parent: %s, Term: %s, Magnitude: %g)' % (self.parent.key,
                                                                              self.key,
                                                                              self.magnitude)


class ObservedBgFlow(ObservedFragmentFlow):
    @property
    def bg_key(self):
        return self.ff.term.term_node, self.ff.term.term_flow, self.ff.term.direction

    def __str__(self):
        return 'ObservedBg(Parent: %s, Term: %s, Magnitude: %g)' % (self.parent.key, self.bg_key, self.magnitude)


class ObservedEmFlow(ObservedFragmentFlow):
    @property
    def locale(self):
        try:
            return self.ff.fragment['SpatialScope']
        except KeyError:
            return ''

    @property
    def context(self):
        return self.term.term_node

    def __str__(self):
        return 'ObservedEm(Flow: %s, Context: %s, Magnitude: %g)' % (self.flow, self.context, self.magnitude)


class ObservedCutoff(object):
    """
    Because of some complexities involving traversal- namely the "descend" switch and the accompanying need to indicate
    exchanges with enclosed subfragments, cutoffs are a special class that does not inherit from ObservedFlow.  This
    is probably a bad move and I may want to refactor this. (but I need TESTS first!)
    """
    @classmethod
    def from_off(cls, off, negate=False):
        return cls(off.parent, off.flow, off.direction, off.ff.magnitude, negate=negate)

    @classmethod
    def from_exchange(cls, parent, exch):
        mag = parent.magnitude * exch.value
        return cls(parent, exch.flow, exch.direction, mag)

    def __init__(self, parent, flow, direction, magnitude, negate=False):
        """

        :param parent:
        :param flow:
        :param direction:
        :param magnitude:
        :param negate: [False]
        """
        self.parent = parent
        self.flow = flow
        self.direction = direction
        self.magnitude = magnitude
        self.negate = negate

    @property
    def key(self):
        if self.negate:
            return tuple(self.parent.key + (self.flow.external_ref, 'negated'))
        else:
            return tuple(self.parent.key + (self.flow.external_ref,))

    @property
    def value(self):
        val = self.magnitude / self.parent.magnitude
        if self.negate:
            val *= -1
        return val

    @property
    def cutoff_key(self):
        return self.flow, self.direction, self.parent.locale

    @property
    def cutoff_key(self):
        return self.flow, self.direction, self.parent.locale

    @property
    def external_ref(self):
        return self.flow.external_ref

    def __repr__(self):
        return str(self)

    def __str__(self):
        if self.negate:
            mag = '-%g [negated]' % self.magnitude
        else:
            mag = '%g' % self.magnitude
        return 'ObservedCutoff(Parent: %s, %s: %s, Magnitude: %s)' % (self.parent.key, self.direction,
                                                                      self.flow, mag)


class TraversalObserver(Observer):
    """
    Take a sequence of fragmentflows and processes them into an Af, Ad, and Bf
    """

    def __init__(self, fragment_flows, **kwargs):
        """
        Each incoming fragment flow implies the existence of:
         - a distinct foreground flow (i.e. column of af) as the ff's parent - always known or None
         - a distinct row in Af, Ad, or Bf, as the term - always determinable from the fragment

        so we ensure
        from that we create an observed fragment flow
        :param fragment_flows:
        """
        super(TraversalObserver, self).__init__(**kwargs)

        self._ffqueue = deque(fragment_flows)  # once thru

        self._frags_seen = dict()  # maps to key of ffid
        self._descend_targets = dict()  # maps descend fragment to its most recent parent

        self._deferred_frag_queue = deque()  # for non-descend subfragments, for later

        self._ffs = []

        self._descents = []  # add ffids
        self._parents = []  # keep a stack of OFFs

    def __next__(self):
        return self.next_ff()

    def _make_key(self, ffid):
        return tuple(self._descents + [ffid])

    def _add_parent(self, parent):
        self._print('Adding parent %s' % parent)
        self._parents.append(parent)

    def _pop_parent(self):
        pop = self._parents.pop()
        self._print('Popped parent %s' % pop)
        return pop

    @property
    def _current_parent(self):
        try:
            return self._parents[-1]
        except IndexError:
            return RX

    def _traverse_node(self, off):
        self._add_foreground(off)
        self._add_parent(off)

    '''
    Subfragment handling
    '''
    def _descend(self, off):
        """

        :param off: the parent of a descend fragment
        :return:
        """
        if off.ff.term.term_node in self._descend_targets:
            raise DescentCollision(off)
        self._print(' # descending %d' % off.ffid)
        self._descents.append(off.ffid)
        self._descend_targets[off.ff.term.term_node] = off

    def _defer(self, off):
        """

        :param off: the parent of a non-descend fragment-- gets handled after current traversal is finished
        :return:
        """
        self._deferred_frag_queue.append(off)

    def _add_subfrag_dependency(self, off, tgt):
        """
        The off is the parent, the off.term.term_node is the term fragment; tgt is the KEY of the term fragment
        :param off:
        :return:
        """
        dep = ObservedFragmentFlow(off.ff, tgt)
        dep.observe(off)
        self._Af.append(dep)

    def _feed_deferred_frag(self):
        """
        Processes the deferred fragment queue-
         - if the queue is empty, returns False
         - if the queue is nonempty:
            = if the target frag has already been seen, add the deferred dependency and then go back to the queue
            = otherwise, send the cached subfragments into the ff queue and return the deferred off
              (deferred dependency must be added after next ffid has been created)
\        """
        while 1:
            try:
                # deferred is an off whose term is a non-descend subfrag
                deferred = self._deferred_frag_queue.popleft()
            except IndexError:
                return False

            if deferred.term.term_node in self._frags_seen:
                self._add_subfrag_dependency(deferred, self._frags_seen[deferred.term.term_node])
            else:
                # re-traversal is necessary to properly locate cutoffs
                ffs = deferred.term.term_node.traverse(**deferred.ff.subfragment_params)
                self._ffqueue.extend(ffs)
                return deferred

    def _get_next_fragment_flow(self):
        deferred = None
        try:
            ff = self._ffqueue.popleft()
        except IndexError:
            deferred = self._feed_deferred_frag()  # deferred is either False or a FragmentFlow popped from the queue
            if deferred:
                ff = self._ffqueue.popleft()
            else:
                raise EmptyFragQueue

        ffid = len(self._ffs)
        self._ffs.append(ff)

        new_off = ObservedFragmentFlow(self._ffs[ffid], self._make_key(ffid))

        if deferred:
            self._add_subfrag_dependency(deferred, new_off.key)

        return new_off

    def next_ff(self):
        try:
            off = self._get_next_fragment_flow()
        except EmptyFragQueue:
            assert len(self._descend_targets) == 0
            raise StopIteration  ## https://www.python.org/dev/peps/pep-0479/ does not apply because __next__ is iterator
        self._print(off.ff)

        if off.ff.magnitude == 0:
            self._print('Dropping zero-weighted node')
            return self.next_ff()

        # new fragment--
        if off.ff.fragment.reference_entity is None:
            assert off.ff.fragment not in self._frags_seen
            off.observe(RX)
            self._frags_seen[off.ff.fragment] = off.key
            if off.ff.fragment in self._descend_targets:
                parent = self._descend_targets.pop(off.ff.fragment)
                self._add_subfrag_dependency(parent, off.key)

        else:
            # Pop back through parents until we find the current OFF's parent
            while off.ff.fragment.reference_entity is not self._current_parent.fragment:
                try:
                    oldparent = self._pop_parent()
                except IndexError:
                    print('Ran out of parents to pop!')
                    print(off)
                    print(off.ff)
                    raise

                # need this to detect when we've fallen off the end of a descended subfragment
                if len(self._descents) > 0:
                    if self._ffs[self._descents[-1]].fragment is oldparent.fragment:
                        y = self._descents.pop()
                        self._print(' # popped descent %d' % y)

            parent = self._current_parent  # last-seen fragment matching parent is ours!

            off.observe(parent)

            if parent.term.is_subfrag and not parent.term.descend:
                if off.ff.term.is_null:
                    # drop cutoffs from nondescend subfrags because they get traversed later
                    self._print('Dropping enclosed cutoff')
                    return self.next_ff()  # go on to the next ff
                # otherwise we need to "borrow" from their cutoffs to continue our current op

                self._handle_term(off)  # off gets observed here

                oco = ObservedCutoff.from_off(off, negate=True)
                self._add_cutoff(oco, ' * negated')
                return off

        return self._handle_term(off)

    def _handle_term(self, off):
        """
        Upon arrival here, the last entry in self._parents should be our column; our ff determines the rest

        the term can be any of the following:
         * null -> cutoff (parent stays same)
         * bg -> add ad (parent stays same)

         * fg process -> traverse, add unobserved exchanges as emissions

         * fg -> traverse
         * nondescending subfrag -> traverse, add to deferred list
         * descending subfrag -> traverse, add to _descents, add term to _parents

        :param off: the observed fragment flow
        :return:
        """
        if off.ff.term.is_null:
            self._add_cutoff(ObservedCutoff.from_off(off))
        elif off.ff.term.term_is_bg or off.ff.fragment.is_background:
            self._add_background(off.observe_bg_flow())
        elif off.ff.term.is_emission:
            self._add_emission(off.observe_em_flow())
        else:
            self._traverse_node(off)  # make it the parent
            if off.ff.term.is_subfrag:
                # self._add_parent(ProxyParent(off))
                if off.ff.term.descend:
                    self._descend(off)
                else:
                    self._defer(off)
            else:
                # add unobserved exchanges--
                for x in off.ff.term._unobserved_exchanges():  # another argument to expose unobserved_exchanges
                    emf = ObservedExchange(x, off)
                    self._add_emission(emf)

        return off
