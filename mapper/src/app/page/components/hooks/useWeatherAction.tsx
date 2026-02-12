"use client";

import { useCopilotAction } from "@copilotkit/react-core";
import { WeatherCard } from "../WeatherCard";

export function useWeatherAction(themeColor: string) {
  useCopilotAction({
    name: "get_weather",
    description: "Get the weather for a given location.",
    available: "disabled",
    parameters: [
      { name: "location", type: "string", required: true },
    ],
    render: ({ args }) => {
      return <WeatherCard location={args.location} themeColor={themeColor} />
    },
  });
}