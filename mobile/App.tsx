
import React, { useState, useEffect, useRef } from "react";
import {
  SafeAreaView,
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ScrollView,
  StyleSheet,
  StatusBar,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator,
} from "react-native";

const API_BASE_URL = "http://127.0.0.1:8000";

type ChatMessage = {
  id: number;
  role: "user" | "assistant";
  content: string;
};

type Task = {
  id: number;
  title: string;
  description: string;
  completed: boolean;
  created_at: string;
  due_at?: string | null;
};

type Tab = "chat" | "tasks";

export default function App() {
  const [activeTab, setActiveTab] = useState<Tab>("chat");
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const [tasks, setTasks] = useState<Task[]>([]);
  const [tasksLoading, setTasksLoading] = useState(false);
  const [tasksError, setTasksError] = useState("");
  const [updatingTaskId, setUpdatingTaskId] = useState<number | null>(null);

  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 1,
      role: "assistant",
      content:
        "Hi! I'm your AI task assistant. I can create, update, delete, and schedule tasks. What would you like to do?",
    },
  ]);

  const scrollViewRef = useRef<ScrollView>(null);
  const messageIdRef = useRef(1);

  function nextMessageId(): number {
    messageIdRef.current += 1;
    return messageIdRef.current;
  }

  // Load tasks from PostgreSQL through FastAPI.
  async function fetchTasks() {
    setTasksLoading(true);
    setTasksError("");

    try {
      const response = await fetch(`${API_BASE_URL}/tasks`);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();

      // Support both API response formats.
      if (Array.isArray(data)) {
        setTasks(data);
      } else if (data && Array.isArray(data.tasks)) {
        setTasks(data.tasks);
      } else {
        throw new Error("Unexpected tasks response format");
      }
    } catch (error) {
      console.error("Could not load tasks:", error);
      setTasksError(
        "Could not load tasks. Check that FastAPI and PostgreSQL are running."
      );
    } finally {
      setTasksLoading(false);
    }
  }

  // Toggle task completion using the FastAPI PATCH endpoint.
  async function toggleTask(task: Task) {
    if (updatingTaskId !== null) return;

    setUpdatingTaskId(task.id);
    setTasksError("");

    try {
      const response = await fetch(
        `${API_BASE_URL}/tasks/${task.id}`,
        {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            completed: !task.completed,
          }),
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      // Refresh cards using the saved database values.
      await fetchTasks();
    } catch (error) {
      console.error("Could not update task:", error);
      setTasksError(
        "Could not update task. Please try again."
      );
    } finally {
      setUpdatingTaskId(null);
    }
  }

  // Load tasks when the application starts.
  useEffect(() => {
    fetchTasks();
  }, []);

  // Automatically scroll to the latest chat message.
  useEffect(() => {
    if (activeTab === "chat") {
      scrollViewRef.current?.scrollToEnd({
        animated: true,
      });
    }
  }, [messages, loading, activeTab]);

  function switchTab(tab: Tab) {
    setActiveTab(tab);

    if (tab === "tasks") {
      fetchTasks();
    }
  }

  // Send a message to the AI Supervisor Agent.
  async function sendMessage() {
    const message = input.trim();

    if (!message || loading) return;

    const userMessage: ChatMessage = {
      id: nextMessageId(),
      role: "user",
      content: message,
    };

    setMessages((previous) => [...previous, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data: { response: string } = await response.json();

      const assistantMessage: ChatMessage = {
        id: nextMessageId(),
        role: "assistant",
        content: data.response,
      };

      setMessages((previous) => [
        ...previous,
        assistantMessage,
      ]);

      // Reload task data after AI actions.
      await fetchTasks();
    } catch (error) {
      console.error("AI chat request failed:", error);

      const errorMessage: ChatMessage = {
        id: nextMessageId(),
        role: "assistant",
        content:
          "Sorry, I couldn't reach the AI server. Check FastAPI, Ollama, and PostgreSQL.",
      };

      setMessages((previous) => [
        ...previous,
        errorMessage,
      ]);
    } finally {
      setLoading(false);
    }
  }

  // Render a structured task card.
  function renderTask(task: Task) {
    const isUpdating = updatingTaskId === task.id;

    return (
      <View key={task.id} style={styles.taskCard}>
        <View style={styles.taskTitleRow}>
          <TouchableOpacity
            onPress={() => toggleTask(task)}
            disabled={updatingTaskId !== null}
            accessibilityRole="checkbox"
            accessibilityState={{
              checked: task.completed,
              disabled: updatingTaskId !== null,
            }}
            accessibilityLabel={`Mark ${task.title} as ${
              task.completed ? "incomplete" : "completed"
            }`}
            style={[
              styles.taskIndicator,
              task.completed && styles.completedIndicator,
            ]}
          >
            {isUpdating ? (
              <ActivityIndicator
                size="small"
                color={task.completed ? "#FFFFFF" : "#2563EB"}
              />
            ) : (
              <Text style={styles.taskIndicatorText}>
                {task.completed ? "✓" : ""}
              </Text>
            )}
          </TouchableOpacity>

          <Text
            style={[
              styles.taskTitle,
              task.completed && styles.completedTaskTitle,
            ]}
          >
            {task.title}
          </Text>
        </View>

        {task.description ? (
          <Text style={styles.taskDescription}>
            {task.description}
          </Text>
        ) : null}

        <View style={styles.taskFooter}>
          <View
            style={[
              styles.statusBadge,
              task.completed
                ? styles.completedBadge
                : styles.pendingBadge,
            ]}
          >
            <Text
              style={[
                styles.statusBadgeText,
                task.completed
                  ? styles.completedBadgeText
                  : styles.pendingBadgeText,
              ]}
            >
              {task.completed ? "Completed" : "To do"}
            </Text>
          </View>

          <Text style={styles.taskId}>
            Task #{task.id}
          </Text>
        </View>

        {task.due_at ? (
          <Text style={styles.dueDate}>
            Due: {new Date(task.due_at).toLocaleString()}
          </Text>
        ) : null}
      </View>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" />

      <KeyboardAvoidingView
        style={styles.container}
        behavior={Platform.OS === "ios" ? "padding" : undefined}
      >
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.headerTitle}>
            AI Task Manager
          </Text>

          <Text style={styles.headerSubtitle}>
            Your intelligent productivity assistant
          </Text>
        </View>

        {/* Navigation */}
        <View style={styles.tabBar}>
          <TouchableOpacity
            style={[
              styles.tabButton,
              activeTab === "chat" && styles.activeTab,
            ]}
            onPress={() => switchTab("chat")}
          >
            <Text
              style={[
                styles.tabText,
                activeTab === "chat" && styles.activeTabText,
              ]}
            >
              Chat
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[
              styles.tabButton,
              activeTab === "tasks" && styles.activeTab,
            ]}
            onPress={() => switchTab("tasks")}
          >
            <Text
              style={[
                styles.tabText,
                activeTab === "tasks" && styles.activeTabText,
              ]}
            >
              My Tasks ({tasks.length})
            </Text>
          </TouchableOpacity>
        </View>

        {activeTab === "chat" ? (
          <>
            {/* Chat messages */}
            <ScrollView
              ref={scrollViewRef}
              style={styles.contentArea}
              contentContainerStyle={styles.chatMessages}
              keyboardShouldPersistTaps="handled"
              onContentSizeChange={() =>
                scrollViewRef.current?.scrollToEnd({
                  animated: true,
                })
              }
            >
              {messages.map((message) => (
                <View
                  key={message.id}
                  style={[
                    styles.messageBubble,
                    message.role === "user"
                      ? styles.userBubble
                      : styles.assistantBubble,
                  ]}
                >
                  <Text
                    style={[
                      styles.messageText,
                      message.role === "user"
                        ? styles.userText
                        : styles.assistantText,
                    ]}
                  >
                    {message.content}
                  </Text>
                </View>
              ))}

              {loading && (
                <View
                  style={[
                    styles.messageBubble,
                    styles.assistantBubble,
                  ]}
                >
                  <Text style={styles.loadingText}>
                    AI is thinking...
                  </Text>
                </View>
              )}
            </ScrollView>

            {/* Chat input */}
            <View style={styles.inputArea}>
              <TextInput
                style={styles.input}
                placeholder="Ask your AI assistant..."
                placeholderTextColor="#94A3B8"
                value={input}
                onChangeText={setInput}
                onSubmitEditing={sendMessage}
                returnKeyType="send"
                editable={!loading}
              />

              <TouchableOpacity
                style={[
                  styles.sendButton,
                  loading && styles.disabledButton,
                ]}
                onPress={sendMessage}
                disabled={loading}
              >
                <Text style={styles.sendButtonText}>
                  {loading ? "..." : "Send"}
                </Text>
              </TouchableOpacity>
            </View>
          </>
        ) : (
          /* Tasks screen */
          <ScrollView
            style={styles.contentArea}
            contentContainerStyle={styles.tasksContent}
          >
            <View style={styles.tasksHeading}>
              <View>
                <Text style={styles.sectionTitle}>
                  My Tasks
                </Text>

                <Text style={styles.sectionSubtitle}>
                  {tasks.filter((task) => task.completed).length} of{" "}
                  {tasks.length} completed
                </Text>
              </View>

              <TouchableOpacity
                style={styles.refreshButton}
                onPress={fetchTasks}
                disabled={tasksLoading}
              >
                <Text style={styles.refreshButtonText}>
                  Refresh
                </Text>
              </TouchableOpacity>
            </View>

            {tasksLoading && (
              <ActivityIndicator
                size="large"
                color="#2563EB"
              />
            )}

            {tasksError ? (
              <Text style={styles.errorText}>
                {tasksError}
              </Text>
            ) : null}

            {!tasksLoading &&
              !tasksError &&
              tasks.length === 0 && (
                <Text style={styles.emptyText}>
                  No tasks yet. Go to Chat and ask your AI
                  assistant to create one!
                </Text>
              )}

            {tasks.map(renderTask)}
          </ScrollView>
        )}
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#F8FAFC",
  },
  header: {
    backgroundColor: "#0F172A",
    paddingHorizontal: 20,
    paddingTop: 24,
    paddingBottom: 20,
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: "bold",
    color: "#FFFFFF",
  },
  headerSubtitle: {
    fontSize: 13,
    color: "#CBD5E1",
    marginTop: 5,
  },
  tabBar: {
    flexDirection: "row",
    backgroundColor: "#FFFFFF",
    padding: 10,
    gap: 8,
    borderBottomWidth: 1,
    borderBottomColor: "#E2E8F0",
  },
  tabButton: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 10,
    alignItems: "center",
    backgroundColor: "#F1F5F9",
  },
  activeTab: {
    backgroundColor: "#2563EB",
  },
  tabText: {
    fontSize: 14,
    fontWeight: "600",
    color: "#64748B",
  },
  activeTabText: {
    color: "#FFFFFF",
  },
  contentArea: {
    flex: 1,
  },
  chatMessages: {
    padding: 16,
    paddingBottom: 24,
    gap: 12,
  },
  messageBubble: {
    maxWidth: "85%",
    padding: 14,
    borderRadius: 16,
  },
  userBubble: {
    alignSelf: "flex-end",
    backgroundColor: "#2563EB",
    borderBottomRightRadius: 4,
  },
  assistantBubble: {
    alignSelf: "flex-start",
    backgroundColor: "#E2E8F0",
    borderBottomLeftRadius: 4,
  },
  messageText: {
    fontSize: 15,
    lineHeight: 22,
  },
  userText: {
    color: "#FFFFFF",
  },
  assistantText: {
    color: "#0F172A",
  },
  loadingText: {
    color: "#64748B",
    fontSize: 14,
    fontStyle: "italic",
  },
  inputArea: {
    flexDirection: "row",
    padding: 12,
    backgroundColor: "#FFFFFF",
    borderTopWidth: 1,
    borderTopColor: "#E2E8F0",
    gap: 10,
  },
  input: {
    flex: 1,
    borderWidth: 1,
    borderColor: "#CBD5E1",
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: 12,
    fontSize: 15,
    color: "#0F172A",
  },
  sendButton: {
    backgroundColor: "#2563EB",
    paddingHorizontal: 20,
    justifyContent: "center",
    borderRadius: 12,
  },
  disabledButton: {
    backgroundColor: "#94A3B8",
  },
  sendButtonText: {
    color: "#FFFFFF",
    fontWeight: "bold",
  },
  tasksContent: {
    padding: 16,
    gap: 12,
  },
  tasksHeading: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 8,
  },
  sectionTitle: {
    fontSize: 22,
    fontWeight: "bold",
    color: "#0F172A",
  },
  sectionSubtitle: {
    fontSize: 13,
    color: "#64748B",
    marginTop: 4,
  },
  refreshButton: {
    backgroundColor: "#E2E8F0",
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 10,
  },
  refreshButtonText: {
    color: "#0F172A",
    fontWeight: "600",
  },
  taskCard: {
    backgroundColor: "#FFFFFF",
    borderWidth: 1,
    borderColor: "#E2E8F0",
    borderRadius: 16,
    padding: 16,
    gap: 12,
  },
  taskTitleRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
  },
  taskIndicator: {
    width: 24,
    height: 24,
    borderRadius: 12,
    borderWidth: 2,
    borderColor: "#94A3B8",
    justifyContent: "center",
    alignItems: "center",
  },
  completedIndicator: {
    backgroundColor: "#16A34A",
    borderColor: "#16A34A",
  },
  taskIndicatorText: {
    color: "#FFFFFF",
    fontSize: 14,
    fontWeight: "bold",
  },
  taskTitle: {
    flex: 1,
    fontSize: 16,
    fontWeight: "bold",
    color: "#0F172A",
  },
  completedTaskTitle: {
    textDecorationLine: "line-through",
    color: "#64748B",
  },
  taskDescription: {
    fontSize: 14,
    lineHeight: 21,
    color: "#64748B",
  },
  taskFooter: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  statusBadge: {
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 20,
  },
  completedBadge: {
    backgroundColor: "#DCFCE7",
  },
  pendingBadge: {
    backgroundColor: "#FEF3C7",
  },
  statusBadgeText: {
    fontSize: 12,
    fontWeight: "600",
  },
  completedBadgeText: {
    color: "#166534",
  },
  pendingBadgeText: {
    color: "#92400E",
  },
  taskId: {
    fontSize: 12,
    color: "#94A3B8",
  },
  dueDate: {
    fontSize: 12,
    color: "#64748B",
  },
  errorText: {
    color: "#DC2626",
    fontSize: 14,
  },
  emptyText: {
    textAlign: "center",
    color: "#64748B",
    marginTop: 30,
    lineHeight: 22,
  },
});
