module.exports = function (api) {
  api.cache(true);
  const isDev = process.env.NODE_ENV === 'development';
  return {
    presets: ['babel-preset-expo'],
    plugins: [
      // Tamagui compiler plugin — only in production builds.
      // In dev mode Tamagui works fine at runtime without it; skipping it
      // avoids the static-config-evaluation error that shows up in dev.
      ...(!isDev
        ? [
            [
              '@tamagui/babel-plugin',
              {
                components: ['tamagui'],
                config: './theme/tamagui.config.ts',
                logTimings: true,
              },
            ],
          ]
        : []),
      // Must be listed last
      'react-native-reanimated/plugin',
    ],
  };
};
