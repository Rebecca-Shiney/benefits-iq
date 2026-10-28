import { AgentRunner, type AgentRunnerRunRequest } from "@copilotkit/runtime/v2";
import { EMPTY } from "rxjs";

// The default runner retains process-global thread history. This demo deliberately
// has no approved conversation retention, so each request streams without a store.
export class StatelessRunner extends AgentRunner {
  run(request: AgentRunnerRunRequest) {
    return request.agent.run(request.input);
  }

  connect() {
    return EMPTY;
  }

  async isRunning() {
    return false;
  }

  async stop() {
    // The browser cancels its own HTTP stream; there is no detached server run.
    return false;
  }
}
