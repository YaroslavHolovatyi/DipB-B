import { Tabs } from 'expo-router';
import { StyleSheet, View, Text } from 'react-native';
import { colors } from '../../theme/colors';

/**
 * Tab icons — using Unicode symbols as lightweight placeholders.
 * Replace with a proper icon library (e.g. @expo/vector-icons or
 * lucide-react-native) once the UI stabilises.
 *
 * Five-tab footer:
 *   Search   — taverns catalogue + map (folds in the old Map tab)
 *   Social   — raids + parties discovery
 *   Create   — host a raid or start a party
 *   Messages — conversation list (friend DMs, party + raid chats)
 *   AI D&D   — Tavern Tales solo adventure
 *
 * Profile is no longer a tab — it is reached from the header avatar on the
 * Search and Social screens.
 */
const ICONS: Record<string, string> = {
  index:    '🔍',
  social:   '🎉',
  create:   '➕',
  messages: '💬',
  tavern:   '🐉',
};

function TabIcon({ name, focused }: { name: string; focused: boolean }) {
  return (
    <View style={tabStyles.iconWrap}>
      <Text style={[tabStyles.emoji, focused && tabStyles.emojiActive]}>
        {ICONS[name] ?? '●'}
      </Text>
    </View>
  );
}

const tabStyles = StyleSheet.create({
  iconWrap:   { alignItems: 'center', justifyContent: 'center' },
  emoji:      { fontSize: 22, opacity: 0.45 },
  emojiActive:{ opacity: 1 },
});

export default function TabsLayout() {
  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarStyle: {
          backgroundColor: colors.bgCardDark,
          borderTopColor:  colors.borderDefaultDark,
          borderTopWidth:  1,
          paddingBottom:   8,
          paddingTop:      6,
          height:          60,
        },
        tabBarActiveTintColor:   colors.brandPrimary,
        tabBarInactiveTintColor: colors.textSecondaryDark,
        tabBarLabelStyle: {
          fontFamily: 'PlusJakartaSans_600SemiBold',
          fontSize:   10,
          marginTop:  2,
        },
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: 'Search',
          tabBarIcon: ({ focused }) => <TabIcon name="index" focused={focused} />,
        }}
      />
      <Tabs.Screen
        name="social"
        options={{
          title: 'Social',
          tabBarIcon: ({ focused }) => <TabIcon name="social" focused={focused} />,
        }}
      />
      <Tabs.Screen
        name="create"
        options={{
          title: 'Create',
          tabBarIcon: ({ focused }) => <TabIcon name="create" focused={focused} />,
        }}
      />
      <Tabs.Screen
        name="messages"
        options={{
          title: 'Messages',
          tabBarIcon: ({ focused }) => <TabIcon name="messages" focused={focused} />,
        }}
      />
      <Tabs.Screen
        name="tavern"
        options={{
          title: 'AI D&D',
          tabBarIcon: ({ focused }) => <TabIcon name="tavern" focused={focused} />,
        }}
      />
    </Tabs>
  );
}
