import { Ionicons } from '@expo/vector-icons';
import { Tabs } from 'expo-router';
import { StyleSheet, View } from 'react-native';
import { colors } from '../../theme/colors';

/**
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
type IoniconName = React.ComponentProps<typeof Ionicons>['name'];

const ICONS: Record<string, IoniconName> = {
  index:    'search',
  social:   'sparkles',
  create:   'add-circle',
  messages: 'chatbubbles',
  tavern:   'dice',
};

function TabIcon({ name, focused }: { name: string; focused: boolean }) {
  return (
    <View style={tabStyles.iconWrap}>
      <Ionicons
        name={ICONS[name] ?? 'ellipse'}
        size={22}
        color={focused ? colors.brandPrimary : colors.textSecondaryDark}
      />
    </View>
  );
}

const tabStyles = StyleSheet.create({
  iconWrap: { alignItems: 'center', justifyContent: 'center' },
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
