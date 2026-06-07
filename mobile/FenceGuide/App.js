import React from "react";
import { SafeAreaView, StyleSheet, Text, View } from "react-native";

export default function App() {
  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.content}>
        <Text style={styles.title}>Fence Guide</Text>
        <Text style={styles.text}>Brug den webbaserede guide fra Windows-programmets trådløse sync.</Text>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#15191d" },
  content: { flex: 1, justifyContent: "center", padding: 24 },
  title: { color: "white", fontSize: 26, fontWeight: "800", textAlign: "center" },
  text: { color: "#d7dee5", fontSize: 16, textAlign: "center", marginTop: 10 },
});
