package burp;

import javax.swing.*;
import java.awt.*;
import java.util.List;

/**
 * Per-request send dialog: project, role, agent mode, and custom instruction.
 */
final class SendOptionsDialog {
    private SendOptionsDialog() {}

    static final class Result {
        final String instruction;
        final String projectId;
        final String role;
        final JySecAIClient.AgentMode agentMode;

        Result(String instruction, String projectId, String role, JySecAIClient.AgentMode agentMode) {
            this.instruction = instruction;
            this.projectId = projectId == null ? "" : projectId;
            this.role = role == null ? "" : role;
            this.agentMode = agentMode;
        }
    }

    private static String lastProjectId = "";
    private static String lastRole = "";
    private static JySecAIClient.AgentMode lastAgentMode = null;

    static Result show(
            Component parent,
            JySecAIClient client,
            JySecAIClient.Config cfg,
            String token,
            String defaultInstruction
    ) {
        JySecAIClient.AgentMode defaultMode = lastAgentMode != null
                ? lastAgentMode
                : JySecAIClient.AgentMode.EINO_SINGLE;

        JPanel panel = new JPanel(new BorderLayout(0, 10));
        panel.setBorder(BorderFactory.createEmptyBorder(4, 4, 0, 4));

        JPanel selectors = new JPanel(new GridBagLayout());
        GridBagConstraints gc = new GridBagConstraints();
        gc.insets = new Insets(4, 6, 4, 6);
        gc.fill = GridBagConstraints.HORIZONTAL;
        gc.weighty = 0;

        JComboBox<JySecAIClient.ProjectOption> projectBox = new JComboBox<>();
        projectBox.addItem(new JySecAIClient.ProjectOption("", "加载中..."));
        projectBox.setEnabled(false);

        JComboBox<JySecAIClient.RoleOption> roleBox = new JComboBox<>();
        roleBox.addItem(new JySecAIClient.RoleOption("", "加载中..."));
        roleBox.setEnabled(false);

        JComboBox<JySecAIClient.AgentMode> agentBox = new JComboBox<>(JySecAIClient.AgentMode.values());
        agentBox.setSelectedItem(defaultMode);
        agentBox.setRenderer(new DefaultListCellRenderer() {
            @Override
            public Component getListCellRendererComponent(JList<?> list, Object value, int index, boolean isSelected, boolean cellHasFocus) {
                super.getListCellRendererComponent(list, value, index, isSelected, cellHasFocus);
                if (value instanceof JySecAIClient.AgentMode) {
                    setText(((JySecAIClient.AgentMode) value).displayName);
                }
                return this;
            }
        });

        // Row 0: labels — 项目 | 角色 | 对话
        gc.gridy = 0;
        gc.weightx = 1.0;

        gc.gridx = 0;
        selectors.add(new JLabel("项目"), gc);
        gc.gridx = 1;
        selectors.add(new JLabel("角色"), gc);
        gc.gridx = 2;
        selectors.add(new JLabel("对话"), gc);

        // Row 1: dropdowns
        gc.gridy = 1;

        gc.gridx = 0;
        selectors.add(projectBox, gc);
        gc.gridx = 1;
        selectors.add(roleBox, gc);
        gc.gridx = 2;
        selectors.add(agentBox, gc);

        JTextArea editor = new JTextArea(
                defaultInstruction == null || defaultInstruction.trim().isEmpty()
                        ? HttpMessageFormatter.defaultInstruction()
                        : defaultInstruction,
                7,
                70
        );
        editor.setLineWrap(true);
        editor.setWrapStyleWord(true);
        editor.setFont(new Font(Font.SANS_SERIF, Font.PLAIN, 13));

        JPanel instructionPanel = new JPanel(new BorderLayout(0, 6));
        instructionPanel.add(new JLabel("测试指令（可针对当前流量修改）："), BorderLayout.NORTH);
        instructionPanel.add(new JScrollPane(editor), BorderLayout.CENTER);

        panel.add(selectors, BorderLayout.NORTH);
        panel.add(instructionPanel, BorderLayout.CENTER);

        Thread loader = new Thread(() -> {
            try {
                List<JySecAIClient.ProjectOption> projects = client.fetchProjects(cfg, token);
                List<JySecAIClient.RoleOption> roles = client.fetchRoles(cfg, token);
                SwingUtilities.invokeLater(() -> populateProjects(projectBox, projects, lastProjectId));
                SwingUtilities.invokeLater(() -> populateRoles(roleBox, roles, lastRole));
            } catch (Exception ex) {
                SwingUtilities.invokeLater(() -> {
                    projectBox.removeAllItems();
                    projectBox.addItem(new JySecAIClient.ProjectOption("", "(加载失败)"));
                    projectBox.setEnabled(true);
                    roleBox.removeAllItems();
                    roleBox.addItem(new JySecAIClient.RoleOption("", "默认"));
                    roleBox.setEnabled(true);
                    JOptionPane.showMessageDialog(parent,
                            "加载项目/角色失败: " + ex.getMessage(),
                            "JySecAI", JOptionPane.WARNING_MESSAGE);
                });
            }
        }, "JySecAI-LoadCatalog");
        loader.start();

        int result = JOptionPane.showConfirmDialog(
                parent,
                panel,
                "发送到 JySecAI",
                JOptionPane.OK_CANCEL_OPTION,
                JOptionPane.PLAIN_MESSAGE
        );
        if (result != JOptionPane.OK_OPTION) {
            return null;
        }

        JySecAIClient.ProjectOption project = (JySecAIClient.ProjectOption) projectBox.getSelectedItem();
        JySecAIClient.RoleOption role = (JySecAIClient.RoleOption) roleBox.getSelectedItem();
        JySecAIClient.AgentMode agentMode = (JySecAIClient.AgentMode) agentBox.getSelectedItem();
        if (agentMode == null) {
            agentMode = defaultMode;
        }

        String instruction = editor.getText();
        if (instruction == null || instruction.trim().isEmpty()) {
            instruction = HttpMessageFormatter.defaultInstruction();
        } else {
            instruction = instruction.trim();
        }

        lastProjectId = project != null ? project.id : "";
        lastRole = role != null ? role.name : "";
        lastAgentMode = agentMode;

        return new Result(instruction, lastProjectId, lastRole, agentMode);
    }

    private static void populateProjects(JComboBox<JySecAIClient.ProjectOption> box,
                                         List<JySecAIClient.ProjectOption> items,
                                         String selectId) {
        box.removeAllItems();
        for (JySecAIClient.ProjectOption item : items) {
            box.addItem(item);
        }
        selectComboById(box, selectId);
        box.setEnabled(true);
    }

    private static void populateRoles(JComboBox<JySecAIClient.RoleOption> box,
                                      List<JySecAIClient.RoleOption> items,
                                      String selectName) {
        box.removeAllItems();
        for (JySecAIClient.RoleOption item : items) {
            box.addItem(item);
        }
        selectComboByName(box, selectName);
        box.setEnabled(true);
    }

    private static void selectComboById(JComboBox<JySecAIClient.ProjectOption> box, String id) {
        if (id == null) id = "";
        for (int i = 0; i < box.getItemCount(); i++) {
            JySecAIClient.ProjectOption item = box.getItemAt(i);
            if (item != null && id.equals(item.id)) {
                box.setSelectedIndex(i);
                return;
            }
        }
        box.setSelectedIndex(0);
    }

    private static void selectComboByName(JComboBox<JySecAIClient.RoleOption> box, String name) {
        if (name == null) name = "";
        for (int i = 0; i < box.getItemCount(); i++) {
            JySecAIClient.RoleOption item = box.getItemAt(i);
            if (item != null && name.equals(item.name)) {
                box.setSelectedIndex(i);
                return;
            }
        }
        box.setSelectedIndex(0);
    }
}
