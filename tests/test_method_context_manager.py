from routix.method_context_manager import DepthIndexTracker, MethodContextManager


def test_depth_index_tracker_increments_per_depth():
    tracker = DepthIndexTracker()
    assert tracker.next_call_count(1) == 1
    assert tracker.next_call_count(1) == 2
    assert tracker.next_call_count(2) == 1
    assert tracker.next_call_count(2) == 2
    assert tracker.next_call_count(3) == 1


def test_depth_index_tracker_resets_above_depth():
    tracker = DepthIndexTracker()
    tracker.next_call_count(1)
    tracker.next_call_count(2)
    tracker.next_call_count(3)
    assert tracker._depth_index == {1: 1, 2: 1, 3: 1}

    tracker.reset_above_depth(2)
    assert tracker._depth_index == {1: 1, 2: 1}


def test_method_context_manager_push_pop_peek():
    manager = MethodContextManager()

    assert manager.peek() == manager.root  # Should return root context name

    manager.push("method1")
    assert manager.peek() == "method1"

    manager.push("method2")
    assert manager.peek() == "method2"
    assert manager.pop() == "method2"

    assert manager.peek() == "method1"
    assert manager.pop() == "method1"

    assert manager.peek() == manager.root  # Should return root context name
    assert manager.pop() == manager.root  # Should return root context name again


def test_method_context_manager_context_of_current_method():
    manager = MethodContextManager()

    manager.push("phase1st")  # depth 1 → index 1
    assert manager.context_of_current_method == "1-phase1st"

    manager.push("initialize")  # depth 2 → index 1
    assert manager.context_of_current_method == "1-phase1st.1-initialize"

    manager.push("train")  # depth 3 → index 1
    assert manager.context_of_current_method == "1-phase1st.1-initialize.1-train"

    manager.pop()
    manager.push("evaluate")  # depth 3 → index 2
    assert manager.context_of_current_method == "1-phase1st.1-initialize.2-evaluate"

    manager.pop()
    manager.pop()
    manager.push("post_init")  # depth 2 → index 2 (since depth 1 was popped and reused)
    assert manager.context_of_current_method == "1-phase1st.2-post_init"

    manager.pop()
    manager.pop()  # back to root
    manager.push("phase2nd")
    assert manager.context_of_current_method == "2-phase2nd"

    manager.push("finalize")  # depth 2 → index 1
    assert manager.context_of_current_method == "2-phase2nd.1-finalize"
